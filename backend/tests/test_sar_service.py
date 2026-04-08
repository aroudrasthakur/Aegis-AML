"""Unit tests for SAR service."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException
from datetime import datetime, timezone

from app.services.sar_service import SARService


class TestSARServiceGeneratePDF:
    """Tests for SARService.generate_sar_pdf method."""

    @patch("app.services.sar_service.get_report")
    @patch("app.services.sar_service.get_network_case")
    @patch("app.services.sar_service.save_sar_pdf")
    @patch("app.services.sar_service.insert_sar_record")
    def test_successful_sar_generation(
        self, mock_insert, mock_save, mock_get_case, mock_get_report
    ):
        """Test successful SAR generation workflow."""
        # Setup mocks
        mock_get_report.return_value = {
            "id": "report-123",
            "case_id": "case-456",
            "explanation": "Test explanation",
        }

        mock_get_case.return_value = {
            "id": "case-456",
            "typology": "peel chain",
            "risk_score": 0.85,
            "total_amount": 50000.0,
            "wallet_addresses": ["0xabc123"],
            "start_time": datetime(2024, 1, 1, tzinfo=timezone.utc),
            "end_time": datetime(2024, 1, 10, tzinfo=timezone.utc),
        }

        mock_save.return_value = (
            MagicMock(),
            "data/processed/sar_reports/sar_report-123.pdf",
        )

        mock_insert.return_value = {
            "id": "sar-789",
            "report_id": "report-123",
            "case_id": "case-456",
            "sar_path": "data/processed/sar_reports/sar_report-123.pdf",
            "status": "draft",
            "generated_at": datetime.now(timezone.utc),
        }

        # Execute
        service = SARService()
        result = service.generate_sar_pdf("report-123")

        # Verify
        assert result["id"] == "sar-789"
        assert result["report_id"] == "report-123"
        assert result["status"] == "draft"

        # Verify mocks were called
        mock_get_report.assert_called_once_with("report-123")
        mock_get_case.assert_called_once_with("case-456")
        mock_save.assert_called_once()
        mock_insert.assert_called_once()

    @patch("app.services.sar_service.get_report")
    def test_raises_404_when_report_not_found(self, mock_get_report):
        """Test that 404 is raised when report doesn't exist."""
        mock_get_report.return_value = None

        service = SARService()

        with pytest.raises(HTTPException) as exc_info:
            service.generate_sar_pdf("nonexistent-report")

        assert exc_info.value.status_code == 404
        assert "Report not found" in exc_info.value.detail

    @patch("app.services.sar_service.get_report")
    @patch("app.services.sar_service.get_network_case")
    def test_raises_404_when_case_not_found(self, mock_get_case, mock_get_report):
        """Test that 404 is raised when case doesn't exist."""
        mock_get_report.return_value = {
            "id": "report-123",
            "case_id": "case-456",
        }
        mock_get_case.return_value = None

        service = SARService()

        with pytest.raises(HTTPException) as exc_info:
            service.generate_sar_pdf("report-123")

        assert exc_info.value.status_code == 404
        assert "Case not found" in exc_info.value.detail

    @patch("app.services.sar_service.get_report")
    @patch("app.services.sar_service.get_network_case")
    def test_raises_400_when_case_missing_required_fields(
        self, mock_get_case, mock_get_report
    ):
        """Test that 400 is raised when case data is incomplete."""
        mock_get_report.return_value = {
            "id": "report-123",
            "case_id": "case-456",
        }

        # Case missing required fields
        mock_get_case.return_value = {
            "id": "case-456",
            # Missing: typology, wallet_addresses
        }

        service = SARService()

        with pytest.raises(HTTPException) as exc_info:
            service.generate_sar_pdf("report-123")

        assert exc_info.value.status_code == 400
        assert "Incomplete case data" in exc_info.value.detail

    @patch("app.services.sar_service.get_report")
    @patch("app.services.sar_service.get_network_case")
    def test_raises_400_when_case_has_empty_wallet_addresses(
        self, mock_get_case, mock_get_report
    ):
        """Test that 400 is raised when case has no wallet addresses."""
        mock_get_report.return_value = {
            "id": "report-123",
            "case_id": "case-456",
        }

        mock_get_case.return_value = {
            "id": "case-456",
            "typology": "peel chain",
            "wallet_addresses": [],  # Empty list
        }

        service = SARService()

        with pytest.raises(HTTPException) as exc_info:
            service.generate_sar_pdf("report-123")

        assert exc_info.value.status_code == 400
        assert "wallet_addresses" in exc_info.value.detail.lower()

    @patch("app.services.sar_service.get_report")
    @patch("app.services.sar_service.get_network_case")
    @patch("app.services.sar_service.save_sar_pdf")
    def test_raises_500_when_pdf_save_fails(
        self, mock_save, mock_get_case, mock_get_report
    ):
        """Test that 500 is raised when PDF save fails."""
        mock_get_report.return_value = {
            "id": "report-123",
            "case_id": "case-456",
            "explanation": "Test",
        }

        mock_get_case.return_value = {
            "id": "case-456",
            "typology": "peel chain",
            "wallet_addresses": ["0xabc123"],
        }

        # Simulate save failure
        mock_save.side_effect = OSError("Disk full")

        service = SARService()

        with pytest.raises(HTTPException) as exc_info:
            service.generate_sar_pdf("report-123")

        assert exc_info.value.status_code == 500
        assert "Failed to save SAR PDF" in exc_info.value.detail

    @patch("app.services.sar_service.get_report")
    @patch("app.services.sar_service.get_network_case")
    @patch("app.services.sar_service.save_sar_pdf")
    @patch("app.services.sar_service.insert_sar_record")
    def test_includes_user_id_in_record(
        self, mock_insert, mock_save, mock_get_case, mock_get_report
    ):
        """Test that user_id is included in SAR record for audit trail."""
        mock_get_report.return_value = {
            "id": "report-123",
            "case_id": "case-456",
            "explanation": "Test",
        }

        mock_get_case.return_value = {
            "id": "case-456",
            "typology": "peel chain",
            "wallet_addresses": ["0xabc123"],
        }

        mock_save.return_value = (MagicMock(), "path/to/sar.pdf")
        mock_insert.return_value = {"id": "sar-789"}

        service = SARService()
        service.generate_sar_pdf("report-123", user_id="user-999")

        # Verify user_id was passed to insert
        call_args = mock_insert.call_args[0][0]
        assert call_args["generated_by"] == "user-999"

    @patch("app.services.sar_service.get_sar_record_by_report_id")
    @patch("app.services.sar_service.get_report")
    @patch("app.services.sar_service.get_network_case")
    @patch("app.services.sar_service.save_sar_pdf")
    @patch("app.services.sar_service.insert_sar_record")
    def test_property_1_service_returns_complete_sar_record(
        self, mock_insert, mock_save, mock_get_case, mock_get_report, mock_get_existing
    ):
        mock_get_existing.return_value = None
        mock_get_report.return_value = {"id": "report-abc", "case_id": "case-abc", "explanation": "x"}
        mock_get_case.return_value = {
            "id": "case-abc",
            "typology": "peel chain",
            "wallet_addresses": ["0xabc"],
            "risk_score": 0.9,
            "total_amount": 1.0,
        }
        mock_save.return_value = (MagicMock(), "data/processed/sar_reports/sar_report-abc.pdf")
        mock_insert.return_value = {
            "id": "sar-abc",
            "report_id": "report-abc",
            "case_id": "case-abc",
            "sar_path": "data/processed/sar_reports/sar_report-abc.pdf",
            "status": "draft",
            "generated_at": datetime.now(timezone.utc),
        }
        service = SARService()
        out = service.generate_sar_pdf("report-abc")
        for key in ("id", "report_id", "case_id", "sar_path", "status", "generated_at"):
            assert key in out

    @patch("app.services.sar_service.get_sar_record_by_report_id")
    @patch("app.services.sar_service.get_report")
    def test_idempotency_returns_existing_record(
        self, mock_get_report, mock_get_by_report
    ):
        """Property 31: repeated generation on same report returns existing SAR."""
        existing = {
            "id": "sar-existing",
            "report_id": "report-123",
            "case_id": "case-456",
            "sar_path": "data/processed/sar_reports/sar_report-123.pdf",
            "status": "draft",
        }
        mock_get_by_report.return_value = existing
        # Should never be called when existing SAR is present.
        mock_get_report.return_value = None

        service = SARService()
        result = service.generate_sar_pdf("report-123")

        assert result == existing
        mock_get_by_report.assert_called_once_with("report-123")
        mock_get_report.assert_not_called()


class TestSARServiceGetMetadata:
    """Tests for SARService.get_sar_metadata method."""

    @patch("app.services.sar_service.get_sar_record")
    def test_returns_sar_metadata(self, mock_get_record):
        """Test successful SAR metadata retrieval."""
        mock_get_record.return_value = {
            "id": "sar-123",
            "report_id": "report-456",
            "status": "draft",
        }

        service = SARService()
        result = service.get_sar_metadata("sar-123")

        assert result["id"] == "sar-123"
        assert result["report_id"] == "report-456"
        mock_get_record.assert_called_once_with("sar-123")

    @patch("app.services.sar_service.get_sar_record")
    def test_raises_404_when_sar_not_found(self, mock_get_record):
        """Test that 404 is raised when SAR doesn't exist."""
        mock_get_record.return_value = None

        service = SARService()

        with pytest.raises(HTTPException) as exc_info:
            service.get_sar_metadata("nonexistent-sar")

        assert exc_info.value.status_code == 404
        assert "SAR not found" in exc_info.value.detail
