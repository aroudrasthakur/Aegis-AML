"""Tests for SAR schema models and model-level validation."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.sar import SARRecord


def _base_record():
    now = datetime.now(timezone.utc)
    return {
        "id": "sar-1",
        "report_id": "report-1",
        "case_id": "case-1",
        "sar_path": "data/processed/sar_reports/sar_report-1.pdf",
        "filing_date": now,
        "status": "draft",
        "generated_at": now,
    }


def test_sar_record_accepts_valid_statuses():
    for status in ("draft", "filed", "rejected"):
        payload = _base_record()
        payload["status"] = status
        rec = SARRecord(**payload)
        assert rec.status == status


def test_sar_record_rejects_invalid_status():
    payload = _base_record()
    payload["status"] = "unknown"
    with pytest.raises(ValidationError):
        SARRecord(**payload)


def test_sar_record_validates_bsa_id_format():
    payload = _base_record()
    payload["bsa_id"] = "12345678-123-12345"
    rec = SARRecord(**payload)
    assert rec.bsa_id == "12345678-123-12345"

    payload["bsa_id"] = "bad-bsa-id"
    with pytest.raises(ValidationError):
        SARRecord(**payload)

