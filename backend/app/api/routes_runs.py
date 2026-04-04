"""Pipeline-run endpoints: upload, start, status, results."""
from __future__ import annotations

import asyncio
from io import BytesIO
from typing import Annotated

import pandas as pd
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.repositories import runs_repo
from app.services.pipeline_run_service import execute_pipeline_run
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

REQUIRED_HEADERS = {"transaction_id", "sender_wallet", "receiver_wallet", "amount", "timestamp"}
MAX_FILES = 3

_active_tasks: dict[str, asyncio.Task] = {}


@router.post("")
async def create_run(
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

    run = runs_repo.create_run(label=label, total_files=len(parsed_frames))
    run_id = run["id"]

    # Hold frames in memory; caller must POST /start to kick off execution.
    _pending_frames[run_id] = parsed_frames

    return {"run_id": run_id, "status": "pending", "total_files": len(parsed_frames)}


_pending_frames: dict[str, list[pd.DataFrame]] = {}


@router.post("/{run_id}/start")
async def start_run(run_id: str):
    """Launch background execution for a pending run."""
    run = runs_repo.get_run(run_id)
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
async def list_runs(page: int = 1, limit: int = 50):
    data, total = runs_repo.list_runs(page, limit)
    return {"runs": data, "total": total, "page": page, "limit": limit}


@router.get("/{run_id}")
async def get_run(run_id: str):
    run = runs_repo.get_run(run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    return run


@router.get("/{run_id}/report")
async def get_run_report(run_id: str):
    report = runs_repo.get_run_report(run_id)
    if not report:
        raise HTTPException(404, "Report not found for this run")
    return report


@router.get("/{run_id}/suspicious")
async def get_suspicious(run_id: str):
    return runs_repo.get_suspicious_txns(run_id)


@router.get("/{run_id}/clusters")
async def get_clusters(run_id: str):
    return runs_repo.get_run_clusters(run_id)


@router.get("/{run_id}/clusters/{cluster_id}/graph")
async def get_cluster_graph(run_id: str, cluster_id: str):
    snap = runs_repo.get_graph_snapshot(run_id, cluster_id)
    if not snap:
        raise HTTPException(404, "Graph snapshot not found")
    return snap


@router.get("/{run_id}/clusters/{cluster_id}/members")
async def get_cluster_members(run_id: str, cluster_id: str):
    return runs_repo.get_cluster_members(cluster_id)
