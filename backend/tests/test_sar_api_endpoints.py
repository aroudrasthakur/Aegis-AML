"""Integration tests for SAR API endpoints."""

from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes_reports import router as reports_router

app = FastAPI()
app.include_router(reports_router, prefix="/api/reports")
client = TestClient(app)


class _FakeSARService:
    def __init__(self, record=None, generate_error: HTTPException | None = None, meta_error: HTTPException | None = None):
        self._record = record or {
            "id": "sar-1",
            "report_id": "report-1",
            "case_id": "case-1",
            "status": "draft",
            "generated_at": "2026-01-01T00:00:00Z",
            "sar_path": "",
        }
        self._generate_error = generate_error
        self._meta_error = meta_error

    def generate_sar_pdf(self, report_id: str):
        if self._generate_error:
            raise self._generate_error
        out = dict(self._record)
        out["report_id"] = report_id
        return out

    def get_sar_metadata(self, sar_id: str):
        if self._meta_error:
            raise self._meta_error
        out = dict(self._record)
        out["id"] = sar_id
        return out


def test_property_generate_endpoint_missing_report_returns_404(monkeypatch):
    svc = _FakeSARService(generate_error=HTTPException(status_code=404, detail="Report not found"))
    monkeypatch.setattr("app.api.routes_reports.get_sar_service", lambda: svc)
    r = client.post("/api/reports/report-missing/generate-sar")
    assert r.status_code == 404


def test_property_generate_endpoint_missing_case_returns_404(monkeypatch):
    svc = _FakeSARService(generate_error=HTTPException(status_code=404, detail="Case not found"))
    monkeypatch.setattr("app.api.routes_reports.get_sar_service", lambda: svc)
    r = client.post("/api/reports/report-1/generate-sar")
    assert r.status_code == 404


def test_property_generate_endpoint_incomplete_case_returns_400(monkeypatch):
    svc = _FakeSARService(generate_error=HTTPException(status_code=400, detail="Incomplete case data"))
    monkeypatch.setattr("app.api.routes_reports.get_sar_service", lambda: svc)
    r = client.post("/api/reports/report-1/generate-sar")
    assert r.status_code == 400


def test_property_download_invalid_sar_id_returns_404(monkeypatch):
    svc = _FakeSARService(meta_error=HTTPException(status_code=404, detail="SAR not found"))
    monkeypatch.setattr("app.api.routes_reports.get_sar_service", lambda: svc)
    r = client.get("/api/reports/sar/sar-missing/download")
    assert r.status_code == 404


def test_property_download_reads_file_from_path_and_sets_content_type(monkeypatch, tmp_path):
    pdf = tmp_path / "sar.pdf"
    pdf.write_bytes(b"%PDF-1.4\nx\n%%EOF")

    svc = _FakeSARService(record={"id": "sar-9", "sar_path": str(pdf)})
    monkeypatch.setattr("app.api.routes_reports.get_sar_service", lambda: svc)
    monkeypatch.setattr("app.api.routes_reports.validate_sar_path", lambda p: True, raising=False)
    monkeypatch.setattr("app.services.sar.storage.validate_sar_path", lambda p: True)

    r = client.get("/api/reports/sar/sar-9/download")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/pdf")
    assert r.content.startswith(b"%PDF-")


def test_property_download_blocks_path_traversal(monkeypatch):
    svc = _FakeSARService(record={"id": "sar-9", "sar_path": "../../etc/passwd"})
    monkeypatch.setattr("app.api.routes_reports.get_sar_service", lambda: svc)
    monkeypatch.setattr("app.services.sar.storage.validate_sar_path", lambda p: False)

    r = client.get("/api/reports/sar/sar-9/download")
    assert r.status_code == 403


def test_e2e_generate_then_download_flow(monkeypatch, tmp_path):
    pdf = tmp_path / "sar_report-55.pdf"
    pdf.write_bytes(b"%PDF-1.4\ndemo\n%%EOF")
    state = {
        "id": "sar-55",
        "report_id": "report-55",
        "case_id": "case-55",
        "status": "draft",
        "generated_at": "2026-01-01T00:00:00Z",
        "sar_path": str(pdf),
    }
    svc = _FakeSARService(record=state)
    monkeypatch.setattr("app.api.routes_reports.get_sar_service", lambda: svc)
    monkeypatch.setattr("app.services.sar.storage.validate_sar_path", lambda p: True)

    gen = client.post("/api/reports/report-55/generate-sar")
    assert gen.status_code == 200
    sar_id = gen.json()["sar_id"]
    dl = client.get(f"/api/reports/sar/{sar_id}/download")
    assert dl.status_code == 200
    assert dl.content.startswith(b"%PDF-")
