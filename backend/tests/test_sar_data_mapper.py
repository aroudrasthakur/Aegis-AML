"""
Unit tests for SAR Data Mapper.

Tests the mapping of internal report/case data to FinCEN SAR template format.
"""

import pytest
from datetime import datetime, timezone

from app.services.sar.data_mapper import SARDataMapper
from app.schemas.sar import SARData, SubjectInfo, ActivityInfo


@pytest.fixture
def mapper():
    """Create a SARDataMapper instance."""
    return SARDataMapper()


@pytest.fixture
def sample_case():
    """Create a sample case dictionary."""
    return {
        "id": "case-123",
        "typology": "peel chain",
        "risk_score": 0.85,
        "total_amount": 50000.00,
        "wallet_addresses": ["0x1234567890abcdef", "0xfedcba0987654321"],
        "start_time": "2024-01-01T00:00:00Z",
        "end_time": "2024-01-31T23:59:59Z",
    }


@pytest.fixture
def sample_report():
    """Create a sample report dictionary."""
    return {
        "id": "report-456",
        "case_id": "case-123",
        "explanation": "This case involves suspicious peel chain activity with multiple transactions.",
    }


class TestMapToSARFormat:
    """Tests for map_to_sar_format method."""

    def test_returns_valid_sar_data(self, mapper, sample_report, sample_case):
        """Test that mapping returns a valid SARData object."""
        result = mapper.map_to_sar_format(sample_report, sample_case)

        assert isinstance(result, SARData)
        assert result.report_id == "report-456"
        assert result.case_id == "case-123"
        assert result.filing_institution is not None
        assert result.subject is not None
        assert result.activity is not None
        assert result.narrative != ""

    def test_preserves_critical_fields(self, mapper, sample_report, sample_case):
        """Test that critical fields are preserved exactly."""
        result = mapper.map_to_sar_format(sample_report, sample_case)

        assert result.report_id == sample_report["id"]
        assert result.case_id == sample_case["id"]
        assert result.activity.total_amount == sample_case["total_amount"]

    def test_handles_missing_optional_fields(self, mapper, sample_report):
        """Test handling of missing optional fields."""
        minimal_case = {
            "id": "case-minimal",
            "wallet_addresses": ["0xabc123"],
        }

        result = mapper.map_to_sar_format(sample_report, minimal_case)

        assert isinstance(result, SARData)
        assert result.case_id == "case-minimal"
        assert result.activity.total_amount == 0.0


class TestMapSubjectInformation:
    """Tests for map_subject_information method."""

    def test_maps_primary_wallet(self, mapper, sample_case):
        """Test that primary wallet is used as subject identification."""
        result = mapper.map_subject_information(sample_case)

        assert isinstance(result, SubjectInfo)
        assert result.identification == "0x1234567890abcdef"
        assert result.subject_type == "Entity"
        assert "0x123456" in result.name

    def test_handles_empty_wallet_list(self, mapper):
        """Test handling of empty wallet addresses list."""
        case = {"wallet_addresses": []}

        result = mapper.map_subject_information(case)

        assert result.identification == "Unknown"
        assert "Unknown" in result.name

    def test_handles_missing_wallet_addresses(self, mapper):
        """Test handling of missing wallet_addresses field."""
        case = {}

        result = mapper.map_subject_information(case)

        assert result.identification == "Unknown"


class TestMapSuspiciousActivity:
    """Tests for map_suspicious_activity method."""

    def test_maps_activity_dates(self, mapper, sample_case):
        """Test that activity dates are parsed correctly."""
        result = mapper.map_suspicious_activity(sample_case)

        assert isinstance(result, ActivityInfo)
        assert isinstance(result.activity_date_from, datetime)
        assert isinstance(result.activity_date_to, datetime)
        assert result.activity_date_from.year == 2024
        assert result.activity_date_to.year == 2024

    def test_maps_total_amount(self, mapper, sample_case):
        """Test that total amount is mapped correctly."""
        result = mapper.map_suspicious_activity(sample_case)

        assert result.total_amount == 50000.00

    def test_maps_typology_to_activity_types(self, mapper, sample_case):
        """Test that typology is converted to SAR activity types."""
        result = mapper.map_suspicious_activity(sample_case)

        assert len(result.activity_type) > 0
        assert "Structuring" in result.activity_type or "Money Laundering" in result.activity_type

    def test_sets_product_and_instrument_types(self, mapper, sample_case):
        """Test that product and instrument types are set correctly."""
        result = mapper.map_suspicious_activity(sample_case)

        assert "Digital Currency" in result.product_type
        assert "Blockchain Transaction" in result.instrument_type

    def test_handles_missing_dates(self, mapper):
        """Test handling of missing date fields."""
        case = {"total_amount": 1000.0}

        result = mapper.map_suspicious_activity(case)

        assert isinstance(result.activity_date_from, datetime)
        assert isinstance(result.activity_date_to, datetime)

    def test_handles_zero_amount(self, mapper):
        """Test handling of zero or missing amount."""
        case = {}

        result = mapper.map_suspicious_activity(case)

        assert result.total_amount == 0.0


class TestMapNarrative:
    """Tests for map_narrative method."""

    def test_generates_non_empty_narrative(self, mapper, sample_report, sample_case):
        """Test that narrative is generated and non-empty."""
        result = mapper.map_narrative(sample_report, sample_case)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_includes_case_id(self, mapper, sample_report, sample_case):
        """Test that narrative includes case ID."""
        result = mapper.map_narrative(sample_report, sample_case)

        assert "case-123" in result

    def test_includes_typology(self, mapper, sample_report, sample_case):
        """Test that narrative includes typology information."""
        result = mapper.map_narrative(sample_report, sample_case)

        assert "peel chain" in result.lower()

    def test_includes_wallet_information(self, mapper, sample_report, sample_case):
        """Test that narrative includes wallet address information."""
        result = mapper.map_narrative(sample_report, sample_case)

        assert "0x1234567890abcdef" in result

    def test_includes_explanation(self, mapper, sample_report, sample_case):
        """Test that narrative includes report explanation."""
        result = mapper.map_narrative(sample_report, sample_case)

        assert "suspicious peel chain activity" in result.lower()

    def test_truncates_long_narrative(self, mapper, sample_report, sample_case):
        """Test that narrative is truncated if it exceeds 10,000 characters."""
        # Create a very long explanation
        long_explanation = "X" * 15000
        long_report = {**sample_report, "explanation": long_explanation}

        result = mapper.map_narrative(long_report, sample_case)

        assert len(result) <= 10000

    def test_handles_missing_explanation(self, mapper, sample_case):
        """Test handling of missing explanation field."""
        report = {"id": "report-789", "case_id": "case-123"}

        result = mapper.map_narrative(report, sample_case)

        assert len(result) > 0
        assert "automated monitoring" in result.lower()


class TestTypologyMapping:
    """Tests for typology to SAR activity type mapping."""

    def test_peel_chain_mapping(self, mapper):
        """Test peel chain typology mapping."""
        result = mapper._map_typology_to_sar_types("peel chain")

        assert "Structuring" in result or "Money Laundering" in result

    def test_fan_out_mapping(self, mapper):
        """Test fan-out typology mapping."""
        result = mapper._map_typology_to_sar_types("fan-out")

        assert len(result) > 0

    def test_cross_chain_mapping(self, mapper):
        """Test cross-chain typology mapping."""
        result = mapper._map_typology_to_sar_types("cross-chain bridge hop")

        assert "Money Laundering" in result or "Terrorist Financing" in result

    def test_unknown_typology_fallback(self, mapper):
        """Test fallback for unknown typology."""
        result = mapper._map_typology_to_sar_types("unknown-typology")

        assert result == ["Money Laundering"]

    def test_case_insensitive_mapping(self, mapper):
        """Test that typology mapping is case-insensitive."""
        result1 = mapper._map_typology_to_sar_types("PEEL CHAIN")
        result2 = mapper._map_typology_to_sar_types("peel chain")

        assert result1 == result2


class TestDateTimeParsing:
    """Tests for datetime parsing."""

    def test_parses_iso_format_string(self, mapper):
        """Test parsing of ISO format datetime string."""
        result = mapper._parse_datetime("2024-01-15T12:30:00Z")

        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_handles_datetime_object(self, mapper):
        """Test handling of datetime object."""
        dt = datetime(2024, 1, 15, 12, 30, 0, tzinfo=timezone.utc)
        result = mapper._parse_datetime(dt)

        assert result == dt

    def test_adds_timezone_to_naive_datetime(self, mapper):
        """Test that timezone is added to naive datetime."""
        dt = datetime(2024, 1, 15, 12, 30, 0)
        result = mapper._parse_datetime(dt)

        assert result.tzinfo is not None

    def test_handles_invalid_string(self, mapper):
        """Test handling of invalid datetime string."""
        result = mapper._parse_datetime("invalid-date")

        assert isinstance(result, datetime)

    def test_handles_unexpected_type(self, mapper):
        """Test handling of unexpected type."""
        result = mapper._parse_datetime(12345)

        assert isinstance(result, datetime)


class TestMapperProperties:
    """Property-style tests for mapper invariants."""

    @pytest.mark.parametrize("typology", [
        "peel chain",
        "fan-out",
        "cross-chain bridge hop",
        "unknown typology",
    ])
    def test_property_3_typology_conversion_valid_codes(self, mapper, typology):
        out = mapper._map_typology_to_sar_types(typology)
        assert isinstance(out, list)
        assert len(out) >= 1
        assert all(isinstance(x, str) and x.strip() for x in out)

    def test_property_2_mapping_preserves_critical_fields(self, mapper, sample_report, sample_case):
        sar = mapper.map_to_sar_format(sample_report, sample_case)
        assert sar.report_id == sample_report["id"]
        assert sar.case_id == sample_case["id"]
        assert sar.activity.total_amount == sample_case["total_amount"]

    def test_property_4_narrative_non_empty(self, mapper, sample_case):
        report = {"id": "r-1", "case_id": "c-1", "explanation": ""}
        narrative = mapper.map_narrative(report, sample_case)
        assert isinstance(narrative, str)
        assert narrative.strip() != ""

    def test_property_5_missing_data_handled_gracefully(self, mapper):
        report = {"id": "r-min", "case_id": "c-min"}
        case = {"id": "c-min", "wallet_addresses": []}
        sar = mapper.map_to_sar_format(report, case)
        assert sar.subject.identification == "Unknown"
        assert sar.activity.total_amount == 0.0

    def test_property_6_mapper_returns_valid_sardata(self, mapper, sample_report, sample_case):
        sar = mapper.map_to_sar_format(sample_report, sample_case)
        assert isinstance(sar, SARData)
        assert isinstance(sar.subject, SubjectInfo)
        assert isinstance(sar.activity, ActivityInfo)
