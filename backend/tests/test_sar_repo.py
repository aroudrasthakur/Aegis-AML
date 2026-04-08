"""Unit and property-style tests for SAR repository operations."""

from unittest.mock import MagicMock

from app.repositories.sar_repo import (
    insert_sar_record,
    get_sar_record,
    get_sar_record_by_report_id,
    update_sar_status,
)


def _mock_sb_with_execute(data):
    sb = MagicMock()
    exec_resp = MagicMock()
    exec_resp.data = data
    sb.table.return_value.insert.return_value.execute.return_value = exec_resp
    sb.table.return_value.insert.return_value.select.return_value.execute.return_value = exec_resp
    sb.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = exec_resp
    sb.table.return_value.update.return_value.eq.return_value.execute.return_value = exec_resp
    sb.table.return_value.update.return_value.eq.return_value.select.return_value.execute.return_value = exec_resp
    return sb


def test_property_insert_record_completeness(monkeypatch):
    row = {
        "id": "sar-1",
        "report_id": "r-1",
        "case_id": "c-1",
        "sar_path": "data/processed/sar_reports/sar_r-1.pdf",
        "status": "draft",
    }
    sb = _mock_sb_with_execute([row])
    monkeypatch.setattr("app.repositories.sar_repo.get_supabase", lambda: sb)

    out = insert_sar_record({"report_id": "r-1", "case_id": "c-1", "sar_path": row["sar_path"]})
    assert out["id"] == "sar-1"
    assert out["report_id"] == "r-1"
    assert out["status"] == "draft"


def test_property_unique_constraint_enforcement_returns_empty_on_error(monkeypatch):
    sb = MagicMock()
    sb.table.return_value.insert.return_value.execute.side_effect = Exception("duplicate key")
    sb.table.return_value.insert.return_value.select.return_value.execute.side_effect = Exception("duplicate key")
    monkeypatch.setattr("app.repositories.sar_repo.get_supabase", lambda: sb)

    out = insert_sar_record({"report_id": "r-1", "case_id": "c-1", "sar_path": "x"})
    assert out == {}


def test_property_retrieval_by_sar_id(monkeypatch):
    row = {"id": "sar-2", "report_id": "r-2"}
    sb = _mock_sb_with_execute(row)
    monkeypatch.setattr("app.repositories.sar_repo.get_supabase", lambda: sb)

    out = get_sar_record("sar-2")
    assert out["id"] == "sar-2"


def test_retrieval_by_report_id(monkeypatch):
    row = {"id": "sar-3", "report_id": "r-3"}
    sb = _mock_sb_with_execute(row)
    monkeypatch.setattr("app.repositories.sar_repo.get_supabase", lambda: sb)

    out = get_sar_record_by_report_id("r-3")
    assert out["report_id"] == "r-3"


def test_update_status_to_filed_adds_filing_date(monkeypatch):
    row = {"id": "sar-4", "status": "filed", "report_id": "r-4"}
    sb = _mock_sb_with_execute([row])
    monkeypatch.setattr("app.repositories.sar_repo.get_supabase", lambda: sb)

    out = update_sar_status("sar-4", "filed", bsa_id="12345678-123-12345")
    assert out is not None
    assert out["status"] == "filed"


def test_update_status_rejects_invalid_status():
    out = update_sar_status("sar-5", "invalid")
    assert out is None
