"""Unit tests for SAR filing institution configuration."""

from app.services.sar.config import (
    get_filing_institution_config,
    validate_filing_institution_config,
)
from app.schemas.sar import FilingInstitution


def test_get_filing_institution_config_from_env(monkeypatch):
    monkeypatch.setenv("FILING_INSTITUTION_NAME", "Aegis AML")
    monkeypatch.setenv("FILING_INSTITUTION_TIN", "12-3456789")
    monkeypatch.setenv("FILING_INSTITUTION_ADDRESS", "100 Main")
    monkeypatch.setenv("FILING_INSTITUTION_CITY", "Austin")
    monkeypatch.setenv("FILING_INSTITUTION_STATE", "TX")
    monkeypatch.setenv("FILING_INSTITUTION_ZIP", "78701")
    monkeypatch.setenv("FILING_INSTITUTION_CONTACT_NAME", "Jane Doe")
    monkeypatch.setenv("FILING_INSTITUTION_CONTACT_PHONE", "555-0101")
    monkeypatch.setenv("FILING_INSTITUTION_CONTACT_EMAIL", "jane@aegis.example")

    cfg = get_filing_institution_config()
    assert cfg.name == "Aegis AML"
    assert cfg.state == "TX"
    assert cfg.contact_email == "jane@aegis.example"


def test_validate_filing_institution_config_rejects_missing_fields():
    cfg = FilingInstitution(
        name="",
        tin="12-3456789",
        address="",
        city="Austin",
        state="TX",
        zip_code="78701",
        contact_name="",
        contact_phone="555-0101",
        contact_email="jane@aegis.example",
    )
    ok, errors = validate_filing_institution_config(cfg)
    assert ok is False
    assert any("name" in e.lower() for e in errors)
    assert any("address" in e.lower() for e in errors)


def test_validate_filing_institution_config_rejects_bad_tin_and_email():
    cfg = FilingInstitution(
        name="Aegis AML",
        tin="123456789",
        address="100 Main",
        city="Austin",
        state="TX",
        zip_code="78701",
        contact_name="Jane Doe",
        contact_phone="555-0101",
        contact_email="not-an-email",
    )
    ok, errors = validate_filing_institution_config(cfg)
    assert ok is False
    assert any("tin" in e.lower() for e in errors)
    assert any("email" in e.lower() for e in errors)

