"""Report generation endpoints."""
from pathlib import Path

from fastapi import APIRouter, HTTPException
from app.repositories.reports_repo import get_reports, get_report
from app.schemas.sar import SARGenerationResponse
from app.services.report_service import generate_case_report, REPORTS_DIR
from app.services.sar_service import get_sar_service
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


@router.post("/{report_id}/generate-sar", response_model=SARGenerationResponse)
async def generate_sar(report_id: str):
    """
    Generate SAR PDF from an existing report.
    
    Args:
        report_id: UUID of the report to generate SAR from
        
    Returns:
        Dictionary containing SAR record with download URL
        
    Raises:
        HTTPException: 404 if report/case not found, 400 if data incomplete,
                      500 if generation fails
                      
    Validates: Requirements 1.1, 1.2, 1.6, 6.1
    """
    try:
        sar_service = get_sar_service()
        sar_record = sar_service.generate_sar_pdf(report_id)
        
        return {
            "sar_id": sar_record["id"],
            "report_id": sar_record["report_id"],
            "case_id": sar_record["case_id"],
            "download_url": f"/api/reports/sar/{sar_record['id']}/download",
            "status": sar_record["status"],
            "generated_at": sar_record["generated_at"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"SAR generation failed for report {report_id}: {e}")
        raise HTTPException(500, "SAR generation failed")


@router.get("/sar/{sar_id}/download")
async def download_sar(sar_id: str):
    """
    Download SAR PDF by SAR ID.
    
    Args:
        sar_id: UUID of the SAR record
        
    Returns:
        FileResponse with PDF content
        
    Raises:
        HTTPException: 404 if SAR not found, 500 if file missing
        
    Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5
    """
    from fastapi.responses import FileResponse
    from app.services.sar.storage import validate_sar_path
    
    try:
        sar_service = get_sar_service()
        sar_record = sar_service.get_sar_metadata(sar_id)
        
        sar_path = sar_record.get("sar_path")
        if not sar_path:
            logger.error(f"SAR record {sar_id} has no sar_path")
            raise HTTPException(404, "SAR file path not found")
        
        # Validate path to prevent path traversal attacks
        if not validate_sar_path(sar_path):
            logger.warning(f"Invalid SAR path detected: {sar_path}")
            raise HTTPException(403, "Access denied")
        
        # Check if file exists
        file_path = Path(sar_path)
        if not file_path.is_file():
            logger.error(f"SAR file not found on disk: {sar_path}")
            raise HTTPException(500, "SAR file not found")
        
        # Log access for audit trail
        logger.info(f"SAR download: sar_id={sar_id}, path={sar_path}")
        
        return FileResponse(
            str(file_path),
            media_type="application/pdf",
            filename=f"sar_{sar_id}.pdf"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"SAR download failed for {sar_id}: {e}")
        raise HTTPException(500, "SAR download failed")
