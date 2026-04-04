"""Pipeline-run endpoints: upload, start, status, results, dashboard stats."""
from __future__ import annotations

import asyncio
import json
from io import BytesIO
from pathlib import Path
from typing import Annotated

import pandas as pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.deps import get_current_user_id
from app.repositories import runs_repo
from app.services.pipeline_run_service import execute_pipeline_run
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

CurrentUserId = Annotated[str, Depends(get_current_user_id)]

REQUIRED_HEADERS = {"transaction_id", "sender_wallet", "receiver_wallet", "amount", "timestamp"}
MAX_FILES = 3

_active_tasks: dict[str, asyncio.Task] = {}
_pending_frames: dict[str, list[pd.DataFrame]] = {}


# ---------------------------------------------------------------------------
# Static paths MUST be declared before /{run_id} to avoid route conflicts
# ---------------------------------------------------------------------------

@router.get("/dashboard/stats")
async def dashboard_stats(user_id: CurrentUserId):
    """Aggregate stats across the current user's runs for dashboard headline cards."""
    all_runs, total_runs = runs_repo.list_runs(page=1, limit=200, user_id=user_id)
    completed = [r for r in all_runs if r.get("status") == "completed"]
    latest = completed[0] if completed else None

    total_txns_scored = sum(r.get("total_txns", 0) for r in completed)
    total_suspicious = sum(r.get("suspicious_tx_count", 0) for r in completed)
    total_clusters = sum(r.get("suspicious_cluster_count", 0) for r in completed)
    total_runs_completed = len(completed)

    latest_suspicious = latest.get("suspicious_tx_count", 0) if latest else 0
    latest_clusters = latest.get("suspicious_cluster_count", 0) if latest else 0
    latest_txns = latest.get("total_txns", 0) if latest else 0

    return {
        "total_runs": total_runs,
        "completed_runs": total_runs_completed,
        "total_txns_scored": total_txns_scored,
        "total_suspicious": total_suspicious,
        "total_clusters": total_clusters,
        "latest_run": latest,
        "latest_suspicious": latest_suspicious,
        "latest_clusters": latest_clusters,
        "latest_txns": latest_txns,
    }


@router.get("/model/metrics")
async def model_metrics():
    """Return trained model metrics from the artifacts directory."""
    for p in [Path("models/artifacts/metrics_report.json"), Path("../models/artifacts/metrics_report.json")]:
        if p.exists():
            try:
                return {"metrics": json.loads(p.read_text())}
            except Exception:
                pass
    return {"metrics": None}


@router.get("/model/threshold")
async def model_threshold():
    """Return threshold config from training artifacts."""
    for p in [Path("models/artifacts/threshold_config.json"), Path("../models/artifacts/threshold_config.json")]:
        if p.exists():
            try:
                return {"threshold": json.loads(p.read_text())}
            except Exception:
                pass
    return {"threshold": None}


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

@router.post("")
async def create_run(
    user_id: CurrentUserId,
    files: Annotated[list[UploadFile], File(description="Up to 3 CSV files")],
    label: Annotated[str | None, Form()] = None,
):
    """Upload up to 3 CSVs, validate, create a pending pipeline run."""
    if len(files) > MAX_FILES:
        raise HTTPException(400, f"Maximum {MAX_FILES} files per run")
    if not files:
        raise HTTPException(400, "At least one CSV file is required")

    parsed_frames: list[pd.DataFrame] = []
    errors: list[dict] = []

    for f in files:
        fname = f.filename or "unknown"
        if not fname.lower().endswith(".csv"):
            errors.append({"file": fname, "error": "File must be a .csv"})
            continue
        raw = await f.read()
        try:
            df = pd.read_csv(BytesIO(raw))
        except Exception as exc:
            errors.append({"file": fname, "error": f"Cannot parse CSV: {exc}"})
            continue
        missing = REQUIRED_HEADERS - set(df.columns)
        if missing:
            errors.append({"file": fname, "error": f"Missing required headers: {sorted(missing)}"})
            continue
        parsed_frames.append(df)

    if errors:
        raise HTTPException(400, detail={"message": "Validation failed", "file_errors": errors})

    run = runs_repo.create_run(label=label, total_files=len(parsed_frames), user_id=user_id)
    run_id = run["id"]
    _pending_frames[run_id] = parsed_frames

    return {"run_id": run_id, "status": "pending", "total_files": len(parsed_frames)}


@router.post("/{run_id}/start")
async def start_run(run_id: str, user_id: CurrentUserId):
    """Launch background execution for a pending run."""
    run = runs_repo.get_run(run_id, user_id)
    if not run:
        raise HTTPException(404, "Run not found")
    if run["status"] != "pending":
        raise HTTPException(400, f"Run is already {run['status']}")

    frames = _pending_frames.pop(run_id, None)
    if not frames:
        raise HTTPException(400, "No uploaded data found for this run. Re-upload files.")

    task = asyncio.create_task(execute_pipeline_run(run_id, frames))
    _active_tasks[run_id] = task

    def _cleanup(t: asyncio.Task) -> None:
        _active_tasks.pop(run_id, None)

    task.add_done_callback(_cleanup)

    return {"run_id": run_id, "status": "running"}


@router.get("")
async def list_runs(user_id: CurrentUserId, page: int = 1, limit: int = 50):
    data, total = runs_repo.list_runs(page, limit, user_id=user_id)
    return {"runs": data, "total": total, "page": page, "limit": limit}


@router.get("/{run_id}")
async def get_run(run_id: str, user_id: CurrentUserId):
    run = runs_repo.get_run(run_id, user_id)
    if not run:
        raise HTTPException(404, "Run not found")
    return run


@router.get("/{run_id}/scores")
async def get_run_scores(run_id: str, user_id: CurrentUserId):
    """Return all score rows for a given run."""
    if not runs_repo.get_run(run_id, user_id):
        raise HTTPException(404, "Run not found")
    return runs_repo.get_run_scores(run_id)


@router.get("/{run_id}/report")
async def get_run_report(run_id: str, user_id: CurrentUserId):
    if not runs_repo.get_run(run_id, user_id):
        raise HTTPException(404, "Run not found")
    report = runs_repo.get_run_report(run_id)
    if not report:
        raise HTTPException(404, "Report not found for this run")
    return report


@router.get("/{run_id}/report/summary")
async def get_report_summary(run_id: str, user_id: CurrentUserId):
    """Return cached LLM summary for a run report (200 with nulls if not generated yet)."""
    if not runs_repo.get_run(run_id, user_id):
        raise HTTPException(404, "Run not found")
    from app.services.summary_service import get_run_report_summary
    result = get_run_report_summary(run_id)
    if not result:
        return {
            "summary_text": None,
            "summary_model": None,
            "summary_generated_at": None,
            "cached": False,
        }
    return {**result, "cached": True}


@router.post("/{run_id}/report/summary")
async def generate_report_summary(run_id: str, user_id: CurrentUserId, force: bool = False):
    """Generate an LLM summary for a run report (idempotent unless force=true)."""
    if not runs_repo.get_run(run_id, user_id):
        raise HTTPException(404, "Run not found")
    from app.services.summary_service import generate_run_report_summary
    try:
        return await asyncio.get_running_loop().run_in_executor(
            None, lambda: generate_run_report_summary(run_id, force=force)
        )
    except ValueError as e:
        raise HTTPException(404, str(e))
    except RuntimeError as e:
        raise HTTPException(503, str(e))


@router.get("/{run_id}/suspicious")
async def get_suspicious(run_id: str, user_id: CurrentUserId):
    if not runs_repo.get_run(run_id, user_id):
        raise HTTPException(404, "Run not found")
    return runs_repo.get_enriched_suspicious_txns(run_id)


@router.get("/{run_id}/wallets")
async def get_run_wallets(run_id: str, user_id: CurrentUserId):
    """Aggregate wallet-level data from cluster members, scores, and suspicious txns."""
    run = runs_repo.get_run(run_id, user_id)
    if not run:
        raise HTTPException(404, "Run not found")
    return runs_repo.get_run_wallets(run_id)


@router.get("/{run_id}/clusters")
async def get_clusters(run_id: str, user_id: CurrentUserId):
    if not runs_repo.get_run(run_id, user_id):
        raise HTTPException(404, "Run not found")
    return runs_repo.get_run_clusters(run_id)


@router.get("/{run_id}/clusters/{cluster_id}/graph")
async def get_cluster_graph(run_id: str, cluster_id: str, user_id: CurrentUserId):
    if not runs_repo.get_run(run_id, user_id):
        raise HTTPException(404, "Run not found")
    c = runs_repo.get_cluster(cluster_id)
    if not c or str(c.get("run_id")) != str(run_id):
        raise HTTPException(404, "Cluster not found")
    snap = runs_repo.get_graph_snapshot(run_id, cluster_id)
    if not snap:
        raise HTTPException(404, "Graph snapshot not found")
    return snap


@router.get("/{run_id}/clusters/{cluster_id}/members")
async def get_cluster_members(run_id: str, cluster_id: str, user_id: CurrentUserId):
    if not runs_repo.get_run(run_id, user_id):
        raise HTTPException(404, "Run not found")
    c = runs_repo.get_cluster(cluster_id)
    if not c or str(c.get("run_id")) != str(run_id):
        raise HTTPException(404, "Cluster not found")
    return runs_repo.get_cluster_members(cluster_id)
