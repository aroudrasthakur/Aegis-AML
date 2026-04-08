"""Tests for SAR sectioned layout validation and formatting."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.schemas.sar import SARReportLayout
from app.services.sar.formatter import SARReportFormatter
from app.services.sar.validation import validate_sar_layout_payload


@pytest.fixture
def sample_payload() -> dict:
    fixture = Path(__file__).parent / "fixtures" / "sar_layout_payload.json"
    return json.loads(fixture.read_text(encoding="utf-8"))


def test_valid_sar_creation(sample_payload):
    is_valid, layout, errors = validate_sar_layout_payload(sample_payload)
    assert is_valid is True
    assert errors == []
    assert isinstance(layout, SARReportLayout)
    assert layout.narrative.summary_text.startswith("Initial alert")


def test_missing_required_narrative(sample_payload):
    sample_payload["narrative"]["summary_text"] = "   "
    is_valid, layout, errors = validate_sar_layout_payload(sample_payload)
    assert is_valid is False
    assert layout is None
    assert any("summary_text" in str(e.get("loc", "")) for e in errors)


def test_invalid_date_handling(sample_payload):
    sample_payload["internal_review_actions"]["filing_date"] = "not-a-date"
    is_valid, layout, errors = validate_sar_layout_payload(sample_payload)
    assert is_valid is False
    assert layout is None
    assert any("filing_date" in str(e.get("loc", "")) for e in errors)


def test_invalid_amount_handling(sample_payload):
    sample_payload["suspicious_activity"]["total_amount"] = "abc-not-number"
    is_valid, layout, errors = validate_sar_layout_payload(sample_payload)
    assert is_valid is False
    assert layout is None
    assert any("total_amount" in str(e.get("loc", "")) for e in errors)


def test_rendering_order_of_sections(sample_payload):
    layout = SARReportLayout.model_validate(sample_payload)
    text = SARReportFormatter().render_text(layout)
    expected = [
        "Subject Information",
        "Reporting Institution Details",
        "Suspicious Activity Details",
        "Narrative",
        "Transaction Information",
        "Supporting Documentation",
        "Internal Review and Actions Taken",
        "Law Enforcement Notification",
    ]
    indices = [text.index(section) for section in expected]
    assert indices == sorted(indices)


def test_optional_sections_omitted_gracefully(sample_payload):
    sample_payload["supporting_documentation"]["notes"] = None
    sample_payload["law_enforcement_notification"] = {
        "agency_name": None,
        "notification_date": None,
        "case_reference_number": None,
    }
    layout = SARReportLayout.model_validate(sample_payload)
    text = SARReportFormatter().render_text(layout)
    assert "Supporting Documentation" in text
    assert "Law Enforcement Notification" in text
    assert "N/A" in text


def test_round_trip_serialization(sample_payload):
    original = SARReportLayout.model_validate(sample_payload)
    serialized = original.model_dump(mode="json")
    restored = SARReportLayout.model_validate(serialized)
    assert restored == original
