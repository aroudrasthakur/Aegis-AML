"""Report generation endpoints."""
from pathlib import Path

from fastapi import APIRouter, HTTPException
from app.repositories.reports_repo import get_reports, get_report
from app.services.report_service import generate_case_report, REPORTS_DIR
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("")
async def list_reports():
    return get_reports()


@router.post("/generate/{case_id}")
async def generate_report(case_id: str):
    try:
        report = generate_case_report(case_id)
        if not report:
            raise HTTPException(500, "Report generation failed")
        return report
    except HTTPException:
        raise
    except Exception:
        logger.exception("Report generation failed for case %s", case_id)
        raise HTTPException(500, "Report generation failed")


@router.get("/{report_id}")
async def get_report_detail(report_id: str):
    report = get_report(report_id)
    if not report:
        raise HTTPException(404, "Report not found")
    return report


@router.get("/{report_id}/download")
async def download_report(report_id: str):
    report = get_report(report_id)
    if not report or not report.get("report_path"):
        raise HTTPException(404, "Report not found")
    from fastapi.responses import FileResponse
    resolved = Path(report["report_path"]).resolve()
    allowed_root = REPORTS_DIR.resolve()
    if not str(resolved).startswith(str(allowed_root)):
        raise HTTPException(403, "Access denied")
    if not resolved.is_file():
        raise HTTPException(404, "Report file not found on disk")
    return FileResponse(str(resolved), filename=f"report_{report_id}.json")
