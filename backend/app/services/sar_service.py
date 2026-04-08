"""
SAR Service - Orchestrates SAR PDF generation workflow.

This module provides the SARService class that coordinates data retrieval,
mapping, PDF generation, and storage for Suspicious Activity Reports.
"""

from typing import Optional
from fastapi import HTTPException
from pydantic import ValidationError

from app.repositories.reports_repo import get_report
from app.repositories.network_cases_repo import get_network_case
from app.repositories import runs_repo
from app.repositories.sar_repo import (
    insert_sar_record,
    get_sar_record,
    get_sar_record_by_report_id,
)
from app.services.sar.data_mapper import SARDataMapper
from app.services.sar.pdf_generator import SARPDFGenerator
from app.services.sar.storage import save_sar_pdf
from app.services.sar.security import log_sar_access
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SARService:
    """Orchestrates SAR PDF generation workflow."""

    def __init__(self):
        """Initialize SAR service with required components."""
        self.mapper = SARDataMapper()
        self.generator = SARPDFGenerator()

    def generate_sar_pdf(self, report_id: str, user_id: Optional[str] = None) -> dict:
        """
        Generate SAR PDF from existing report.

        This method coordinates the complete SAR generation workflow:
        1. Retrieve report and case data from database
        2. Map internal data to SAR format
        3. Generate PDF document
        4. Save PDF to storage
        5. Create database record

        Args:
            report_id: UUID of the report to generate SAR from
            user_id: Optional UUID of user generating the SAR (for audit trail)

        Returns:
            Dictionary containing SAR record with fields:
            - id: SAR record UUID
            - report_id: Associated report UUID
            - case_id: Associated case UUID
            - sar_path: File path to SAR PDF
            - status: SAR status ("draft")
            - generated_at: Timestamp of generation

        Raises:
            HTTPException: With appropriate status code and message:
                - 404: Report not found
                - 404: Case not found
                - 400: Incomplete case data
                - 500: PDF generation failed
                - 500: Failed to save SAR PDF
                - 500: Filing institution not configured

        Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 8.3, 8.4
        """
        logger.info(f"Starting SAR generation for report {report_id}")
        
        # Log audit event - generation started
        log_sar_access(
            action="generate_start",
            report_id=report_id,
            user_id=user_id,
            success=True
        )

        try:
            # Step 0: Idempotency - return existing SAR for this report if present.
            existing = get_sar_record_by_report_id(report_id)
            if existing:
                logger.info("Returning existing SAR %s for report %s", existing.get("id"), report_id)
                return existing

            # Step 1: Retrieve report data
            report = get_report(report_id)
            case = None
            case_id = None
            if report:
                # Step 2A: Retrieve network case data for classic report rows.
                case_id = report.get("case_id")
                if not case_id:
                    logger.error(f"Report {report_id} has no associated case_id")
                    log_sar_access(
                        action="generate",
                        report_id=report_id,
                        user_id=user_id,
                        success=False,
                        error_message="Report has no associated case"
                    )
                    raise HTTPException(status_code=400, detail="Report has no associated case")

                case = get_network_case(case_id)
                if not case:
                    logger.error(f"Case not found: {case_id}")
                    log_sar_access(
                        action="generate",
                        report_id=report_id,
                        user_id=user_id,
                        success=False,
                        error_message="Case not found"
                    )
                    raise HTTPException(status_code=404, detail="Case not found")
            else:
                # Step 2B: Fallback for run_reports (pipeline run reports used by dashboard UI).
                try:
                    run_report = runs_repo.get_run_report_by_id(report_id)
                except Exception:
                    logger.exception("Failed run_report lookup for %s", report_id)
                    run_report = None
                if not run_report:
                    logger.error(f"Report not found: {report_id}")
                    log_sar_access(
                        action="generate",
                        report_id=report_id,
                        user_id=user_id,
                        success=False,
                        error_message="Report not found"
                    )
                    raise HTTPException(status_code=404, detail="Report not found")
                report, case = self._build_from_run_report(run_report)
                case_id = case.get("id")

            # Step 3: Validate case has required data
            self._validate_case_data(case)

            # Step 4: Map data to SAR format
            try:
                sar_data = self.mapper.map_to_sar_format(report, case)
            except ValidationError as e:
                logger.error(f"SAR schema validation failed: {e}")
                log_sar_access(
                    action="generate",
                    report_id=report_id,
                    user_id=user_id,
                    success=False,
                    error_message="SAR schema validation failed"
                )
                raise HTTPException(
                    status_code=400,
                    detail={
                        "message": "SAR validation failed",
                        "errors": e.errors(),
                    },
                )
            except ValueError as e:
                logger.error(f"Data mapping failed: {e}")
                log_sar_access(
                    action="generate",
                    report_id=report_id,
                    user_id=user_id,
                    success=False,
                    error_message=f"Data mapping failed: {str(e)}"
                )
                raise HTTPException(status_code=400, detail=f"Data mapping failed: {str(e)}")
            except Exception as e:
                logger.exception(f"Unexpected error during data mapping: {e}")
                log_sar_access(
                    action="generate",
                    report_id=report_id,
                    user_id=user_id,
                    success=False,
                    error_message="Filing institution not configured"
                )
                raise HTTPException(status_code=500, detail="Filing institution not configured")

            # Step 5: Generate PDF
            try:
                pdf_bytes = self.generator.create_sar_pdf(sar_data)
            except Exception as e:
                logger.exception(f"PDF generation failed: {e}")
                log_sar_access(
                    action="generate",
                    report_id=report_id,
                    user_id=user_id,
                    success=False,
                    error_message="PDF generation failed"
                )
                raise HTTPException(status_code=500, detail="PDF generation failed")

            # Step 6: Save PDF to storage
            try:
                _, sar_path = save_sar_pdf(pdf_bytes, report_id)
            except Exception as e:
                logger.exception(f"Failed to save SAR PDF: {e}")
                log_sar_access(
                    action="generate",
                    report_id=report_id,
                    user_id=user_id,
                    success=False,
                    error_message="Failed to save SAR PDF"
                )
                raise HTTPException(status_code=500, detail="Failed to save SAR PDF")

            # Step 7: Create database record
            case_id_for_storage = self._coerce_case_id_for_storage(case_id, report)
            sar_record_data = {
                "report_id": report_id,
                "case_id": case_id_for_storage,
                "sar_path": sar_path,
                "status": "draft",
            }

            # Add user_id for audit trail if provided
            if user_id:
                sar_record_data["generated_by"] = user_id

            sar_record = insert_sar_record(sar_record_data)

            if not sar_record:
                logger.error(f"Failed to create SAR database record for report {report_id}")
                log_sar_access(
                    action="generate",
                    report_id=report_id,
                    user_id=user_id,
                    success=False,
                    error_message="Failed to create SAR record"
                )
                raise HTTPException(status_code=500, detail="Failed to create SAR record")

            logger.info(
                f"Successfully generated SAR {sar_record.get('id')} for report {report_id}"
            )
            
            # Log successful generation
            log_sar_access(
                action="generate",
                sar_id=sar_record.get("id"),
                report_id=report_id,
                user_id=user_id,
                success=True
            )
            
            return sar_record

        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            # Catch any unexpected errors
            logger.exception(f"Unexpected error during SAR generation: {e}")
            log_sar_access(
                action="generate",
                report_id=report_id,
                user_id=user_id,
                success=False,
                error_message="SAR generation failed"
            )
            raise HTTPException(status_code=500, detail="SAR generation failed")

    def get_sar_metadata(self, sar_id: str) -> dict:
        """
        Retrieve SAR generation metadata by SAR ID.

        Args:
            sar_id: UUID of the SAR record

        Returns:
            Dictionary containing SAR record metadata

        Raises:
            HTTPException: 404 if SAR not found

        Validates: Requirements 6.1, 8.4
        """
        logger.debug(f"Retrieving SAR metadata for {sar_id}")
        
        # Log access event
        log_sar_access(
            action="access",
            sar_id=sar_id,
            success=True
        )

        sar_record = get_sar_record(sar_id)

        if not sar_record:
            logger.error(f"SAR not found: {sar_id}")
            log_sar_access(
                action="access",
                sar_id=sar_id,
                success=False,
                error_message="SAR not found"
            )
            raise HTTPException(status_code=404, detail="SAR not found")

        return sar_record

    def get_sar_by_report_id(self, report_id: str) -> Optional[dict]:
        """
        Retrieve SAR record by report ID.

        Args:
            report_id: UUID of the report

        Returns:
            Dictionary containing SAR record, or None if not found
        """
        logger.debug(f"Retrieving SAR for report {report_id}")
        return get_sar_record_by_report_id(report_id)

    def _validate_case_data(self, case: dict) -> None:
        """
        Validate that case has required data for SAR generation.

        Args:
            case: Case dictionary from database

        Raises:
            HTTPException: 400 if case data is incomplete

        Validates: Requirements 7.4
        """
        required_fields = ["id", "typology", "wallet_addresses"]
        missing_fields = []

        for field in required_fields:
            if field not in case or not case[field]:
                missing_fields.append(field)

        if missing_fields:
            logger.error(f"Case missing required fields: {missing_fields}")
            raise HTTPException(
                status_code=400,
                detail=f"Incomplete case data: missing {', '.join(missing_fields)}",
            )

        # Validate wallet_addresses is a non-empty list
        wallet_addresses = case.get("wallet_addresses", [])
        if not isinstance(wallet_addresses, list) or len(wallet_addresses) == 0:
            logger.error("Case has no wallet addresses")
            raise HTTPException(
                status_code=400, detail="Incomplete case data: no wallet addresses"
            )

        logger.debug("Case data validation passed")

    def _build_from_run_report(self, run_report: dict) -> tuple[dict, dict]:
        """Build synthetic report/case payloads from a run_report row for SAR generation."""
        run_id = str(run_report.get("run_id") or "")
        content = run_report.get("content") or {}

        suspicious = runs_repo.get_enriched_suspicious_txns(run_id) if run_id else []
        wallet_set: set[str] = set()
        for row in suspicious:
            sw = str(row.get("sender_wallet") or "").strip()
            rw = str(row.get("receiver_wallet") or "").strip()
            if sw:
                wallet_set.add(sw)
            if rw:
                wallet_set.add(rw)

        cluster_findings = content.get("cluster_findings") or []
        if not wallet_set:
            for cl in cluster_findings:
                cid = cl.get("cluster_id")
                if not cid:
                    continue
                for m in runs_repo.get_cluster_members(str(cid)):
                    addr = str(m.get("wallet_address") or "").strip()
                    if addr:
                        wallet_set.add(addr)

        total_amount = float(
            sum(float(cl.get("total_amount") or 0.0) for cl in cluster_findings)
        )
        typology = "suspicious activity"
        risk_score = 0.5
        if cluster_findings:
            first = cluster_findings[0] or {}
            typology = str(first.get("typology") or typology)
            risk_score = float(first.get("risk_score") or risk_score)

        timestamps = [str(r.get("timestamp") or "") for r in suspicious if r.get("timestamp")]
        start_time = min(timestamps) if timestamps else None
        end_time = max(timestamps) if timestamps else None

        synthetic_case_id = f"run-{run_id or run_report.get('id')}"
        synthetic_report = {
            "id": run_report.get("id"),
            "run_id": run_id,
            "case_id": synthetic_case_id,
            "explanation": (
                f"Pipeline run SAR generated from run report {run_report.get('id')}. "
                f"Suspicious transactions: {len(suspicious)}. "
                f"Clusters: {len(cluster_findings)}."
            ),
        }
        synthetic_case = {
            "id": synthetic_case_id,
            "typology": typology,
            "risk_score": risk_score,
            "total_amount": total_amount,
            "wallet_addresses": sorted(wallet_set),
            "start_time": start_time,
            "end_time": end_time,
            "suspicious_transactions": suspicious,
        }
        return synthetic_report, synthetic_case

    def _coerce_case_id_for_storage(self, case_id: Optional[str], report: dict) -> str:
        """
        Resolve case_id persisted to sar_reports.

        Supports both UUID and synthetic/text case IDs.
        """
        candidates = [
            case_id,
            report.get("run_id"),
            report.get("case_id"),
            report.get("id"),
        ]
        for raw in candidates:
            if not raw:
                continue
            return str(raw)
        raise HTTPException(status_code=500, detail="Unable to resolve case_id for SAR storage")


# Singleton instance for convenience
_sar_service_instance = None


def get_sar_service() -> SARService:
    """
    Get singleton instance of SAR service.

    Returns:
        SARService instance
    """
    global _sar_service_instance
    if _sar_service_instance is None:
        _sar_service_instance = SARService()
    return _sar_service_instance
