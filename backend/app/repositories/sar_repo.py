"""
SAR repository - Database operations for SAR reports.

This module provides database access functions for SAR (Suspicious Activity Report)
records, including insertion, retrieval, and status updates.
"""

from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional

from app.supabase_client import get_supabase
from app.utils.logger import get_logger

logger = get_logger(__name__)


def insert_sar_record(data: dict) -> dict:
    """
    Insert a new SAR record into the database.

    Args:
        data: Dictionary containing SAR record fields:
            - report_id (str, required): UUID of the associated report
            - case_id (str, required): UUID of the associated case
            - sar_path (str, required): File path to the SAR PDF
            - status (str, optional): Status of the SAR (default: "draft")
            - filing_date (datetime, optional): Date when SAR was filed
            - bsa_id (str, optional): BSA identifier from FinCEN
            - generated_by (str, optional): UUID of user who generated the SAR

    Returns:
        Dictionary containing the inserted SAR record with all fields,
        or empty dict if insertion fails

    Validates: Requirements 5.3, 5.4, 5.5
    """
    try:
        sb = get_supabase()

        # Ensure required fields are present
        if not data.get("report_id"):
            logger.error("insert_sar_record: report_id is required")
            return {}

        if not data.get("case_id"):
            logger.error("insert_sar_record: case_id is required")
            return {}

        if not data.get("sar_path"):
            logger.error("insert_sar_record: sar_path is required")
            return {}

        # Set default status if not provided
        if "status" not in data:
            data["status"] = "draft"

        # Insert record. Some postgrest sync builders do not expose `.select()` after
        # insert/update; execute directly for compatibility with the installed client.
        resp = sb.table("sar_reports").insert(data).execute()
        rows = resp.data or []
        if isinstance(rows, dict):
            rows = [rows]
        if not rows:
            # Fallback: some clients return no representation on insert.
            created = get_sar_record_by_report_id(str(data.get("report_id")))
            if created:
                logger.info(
                    "insert_sar_record: Retrieved inserted row via fallback for report %s",
                    data.get("report_id"),
                )
                return created
            logger.error("insert_sar_record: No data returned from insert")
            return {}

        row = rows[0]
        if not isinstance(row, dict):
            logger.error("insert_sar_record: Unexpected row type")
            return {}

        logger.info(f"Inserted SAR record {row.get('id')} for report {data.get('report_id')}")
        return row

    except Exception as e:
        logger.exception(f"insert_sar_record failed: {e}")
        return {}


def get_sar_record(sar_id: str) -> dict | None:
    """
    Retrieve a SAR record by SAR ID.

    Args:
        sar_id: UUID of the SAR record

    Returns:
        Dictionary containing the SAR record, or None if not found

    Validates: Requirements 6.1
    """
    try:
        sb = get_supabase()
        resp = (
            sb.table("sar_reports")
            .select("*")
            .eq("id", sar_id)
            .maybe_single()
            .execute()
        )

        if resp is None or resp.data is None:
            logger.warning(f"SAR record not found: {sar_id}")
            return None

        return resp.data

    except Exception as e:
        logger.exception(f"get_sar_record failed for {sar_id}: {e}")
        return None


def get_sar_record_by_report_id(report_id: str) -> dict | None:
    """
    Retrieve a SAR record by report ID.

    Args:
        report_id: UUID of the associated report

    Returns:
        Dictionary containing the SAR record, or None if not found

    Note: Due to unique constraint on report_id, there can only be one SAR per report.
    """
    try:
        sb = get_supabase()
        resp = (
            sb.table("sar_reports")
            .select("*")
            .eq("report_id", report_id)
            .maybe_single()
            .execute()
        )

        if resp is None or resp.data is None:
            logger.debug(f"No SAR record found for report {report_id}")
            return None

        return resp.data

    except Exception as e:
        logger.exception(f"get_sar_record_by_report_id failed for {report_id}: {e}")
        return None


def update_sar_status(sar_id: str, status: str, bsa_id: Optional[str] = None) -> dict | None:
    """
    Update the status of a SAR record.

    Args:
        sar_id: UUID of the SAR record
        status: New status value ("draft", "filed", "rejected")
        bsa_id: Optional BSA identifier from FinCEN (for "filed" status)

    Returns:
        Dictionary containing the updated SAR record, or None if update fails

    Validates: Requirements 5.3
    """
    try:
        sb = get_supabase()

        # Validate status
        valid_statuses = {"draft", "filed", "rejected"}
        if status not in valid_statuses:
            logger.error(f"Invalid status: {status}. Must be one of {valid_statuses}")
            return None

        # Prepare update data
        update_data = {"status": status}

        # Add filing_date when status changes to "filed"
        if status == "filed":
            update_data["filing_date"] = datetime.now(timezone.utc).isoformat()

        # Add BSA ID if provided
        if bsa_id:
            update_data["bsa_id"] = bsa_id

        # Update record
        resp = (
            sb.table("sar_reports")
            .update(update_data)
            .eq("id", sar_id)
            .execute()
        )

        rows = resp.data or []
        if isinstance(rows, dict):
            rows = [rows]
        if not rows:
            # Fallback for clients that do not return updated representation.
            updated = get_sar_record(sar_id)
            if updated:
                return updated
            logger.warning(f"SAR record not found for update: {sar_id}")
            return None

        row = rows[0]
        if not isinstance(row, dict):
            logger.error("update_sar_status: Unexpected row type")
            return None

        logger.info(f"Updated SAR {sar_id} status to {status}")
        return row

    except Exception as e:
        logger.exception(f"update_sar_status failed for {sar_id}: {e}")
        return None


def get_sar_records_by_status(status: str, limit: int = 50) -> list[dict]:
    """
    Retrieve SAR records by status.

    Args:
        status: Status to filter by ("draft", "filed", "rejected")
        limit: Maximum number of records to return (default: 50)

    Returns:
        List of SAR record dictionaries
    """
    try:
        sb = get_supabase()
        resp = (
            sb.table("sar_reports")
            .select("*")
            .eq("status", status)
            .order("generated_at", desc=True)
            .limit(limit)
            .execute()
        )

        return list(resp.data or [])

    except Exception as e:
        logger.exception(f"get_sar_records_by_status failed for status {status}: {e}")
        return []
