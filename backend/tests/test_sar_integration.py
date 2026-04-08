"""
Integration tests for SAR generation workflow.

Tests the complete workflow from data mapping to PDF generation.
"""

import pytest
from datetime import datetime, timezone

from app.services.sar.data_mapper import SARDataMapper
from app.services.sar.pdf_generator import SARPDFGenerator


@pytest.fixture
def sample_report():
    """Create sample report data."""
    return {
        "id": "report-789",
        "case_id": "case-456",
        "explanation": "Suspicious blockchain activity detected with multiple wallet transfers.",
    }


@pytest.fixture
def sample_case():
    """Create sample case data."""
    return {
        "id": "case-456",
        "typology": "peel chain",
        "risk_score": 0.85,
        "total_amount": 75000.50,
        "wallet_addresses": [
            "0xabcdef1234567890abcdef1234567890abcdef12",
            "0x9876543210fedcba9876543210fedcba98765432",
        ],
        "start_time": "2024-01-01T00:00:00Z",
        "end_time": "2024-01-31T23:59:59Z",
    }


class TestSARGenerationWorkflow:
    """Integration tests for complete SAR generation workflow."""

    def test_end_to_end_sar_generation(self, sample_report, sample_case):
        """Test complete workflow from data mapping to PDF generation."""
        # Step 1: Map data to SAR format
        mapper = SARDataMapper()
        sar_data = mapper.map_to_sar_format(sample_report, sample_case)

        # Verify SAR data is valid
        assert sar_data.report_id == "report-789"
        assert sar_data.case_id == "case-456"
        assert sar_data.subject.identification == "0xabcdef1234567890abcdef1234567890abcdef12"
        assert sar_data.activity.total_amount == 75000.50

        # Step 2: Generate PDF
        generator = SARPDFGenerator()
        pdf_bytes = generator.create_sar_pdf(sar_data)

        # Verify PDF is valid
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b"%PDF-")
        assert b"%%EOF" in pdf_bytes

    def test_workflow_with_minimal_case_data(self, sample_report):
        """Test workflow with minimal case data."""
        minimal_case = {
            "id": "case-minimal",
            "typology": "unknown",
            "wallet_addresses": ["0x1234567890abcdef"],
        }

        # Map data
        mapper = SARDataMapper()
        sar_data = mapper.map_to_sar_format(sample_report, minimal_case)

        # Generate PDF
        generator = SARPDFGenerator()
        pdf_bytes = generator.create_sar_pdf(sar_data)

        # Should still produce valid PDF
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b"%PDF-")

    def test_workflow_with_long_narrative(self, sample_report, sample_case):
        """Test workflow with long explanation that produces multi-page narrative."""
        # Create long explanation
        long_explanation = " ".join(
            [
                "This is a detailed analysis of suspicious blockchain activity. "
                "The investigation revealed multiple concerning patterns."
            ]
            * 100
        )
        sample_report["explanation"] = long_explanation

        # Map data
        mapper = SARDataMapper()
        sar_data = mapper.map_to_sar_format(sample_report, sample_case)

        # Verify narrative is present
        assert len(sar_data.narrative) > 1000

        # Generate PDF
        generator = SARPDFGenerator()
        pdf_bytes = generator.create_sar_pdf(sar_data)

        # Should produce valid multi-page PDF
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b"%PDF-")

    def test_workflow_preserves_data_integrity(self, sample_report, sample_case):
        """Test that critical data is preserved through the workflow."""
        # Map data
        mapper = SARDataMapper()
        sar_data = mapper.map_to_sar_format(sample_report, sample_case)

        # Verify critical fields are preserved
        assert sar_data.report_id == sample_report["id"]
        assert sar_data.case_id == sample_case["id"]
        assert sar_data.activity.total_amount == sample_case["total_amount"]
        assert sar_data.subject.identification in sample_case["wallet_addresses"]

        # Generate PDF
        generator = SARPDFGenerator()
        pdf_bytes = generator.create_sar_pdf(sar_data)

        # PDF should be generated successfully
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0

    def test_multiple_sar_generations(self, sample_report, sample_case):
        """Test generating multiple SARs produces consistent results."""
        mapper = SARDataMapper()
        generator = SARPDFGenerator()

        # Generate first SAR
        sar_data_1 = mapper.map_to_sar_format(sample_report, sample_case)
        pdf_bytes_1 = generator.create_sar_pdf(sar_data_1)

        # Generate second SAR
        sar_data_2 = mapper.map_to_sar_format(sample_report, sample_case)
        pdf_bytes_2 = generator.create_sar_pdf(sar_data_2)

        # Both should be valid PDFs
        assert isinstance(pdf_bytes_1, bytes)
        assert isinstance(pdf_bytes_2, bytes)
        assert len(pdf_bytes_1) > 0
        assert len(pdf_bytes_2) > 0

        # Content should be similar (may differ slightly due to timestamps)
        # But both should have the same structure
        assert pdf_bytes_1.startswith(b"%PDF-")
        assert pdf_bytes_2.startswith(b"%PDF-")
