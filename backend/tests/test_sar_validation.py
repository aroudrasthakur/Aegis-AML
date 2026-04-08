"""Unit tests for SAR validation functions."""

import pytest
from datetime import datetime, timezone, timedelta
from app.services.sar.validation import (
    validate_tin,
    validate_amount,
    validate_date_range,
    validate_narrative_length,
    validate_activity_types,
)


class TestValidateTin:
    """Tests for validate_tin function."""

    def test_valid_tin(self):
        """Test valid EIN format."""
        is_valid, error = validate_tin("12-3456789")
        assert is_valid is True
        assert error == ""

    def test_valid_tin_different_numbers(self):
        """Test valid EIN with different numbers."""
        is_valid, error = validate_tin("99-8765432")
        assert is_valid is True
        assert error == ""

    def test_empty_tin(self):
        """Test empty TIN."""
        is_valid, error = validate_tin("")
        assert is_valid is False
        assert "required" in error.lower()

    def test_none_tin(self):
        """Test None TIN."""
        is_valid, error = validate_tin(None)
        assert is_valid is False
        assert "required" in error.lower()

    def test_invalid_format_no_hyphen(self):
        """Test TIN without hyphen."""
        is_valid, error = validate_tin("123456789")
        assert is_valid is False
        assert "EIN format" in error

    def test_invalid_format_wrong_position_hyphen(self):
        """Test TIN with hyphen in wrong position."""
        is_valid, error = validate_tin("123-456789")
        assert is_valid is False
        assert "EIN format" in error

    def test_invalid_format_too_few_digits(self):
        """Test TIN with too few digits."""
        is_valid, error = validate_tin("12-345678")
        assert is_valid is False
        assert "EIN format" in error

    def test_invalid_format_too_many_digits(self):
        """Test TIN with too many digits."""
        is_valid, error = validate_tin("123-4567890")
        assert is_valid is False
        assert "EIN format" in error

    def test_invalid_format_letters(self):
        """Test TIN with letters."""
        is_valid, error = validate_tin("AB-CDEFGHI")
        assert is_valid is False
        assert "EIN format" in error


class TestValidateAmount:
    """Tests for validate_amount function."""

    def test_valid_positive_integer(self):
        """Test valid positive integer amount."""
        is_valid, error = validate_amount(1000)
        assert is_valid is True
        assert error == ""

    def test_valid_positive_float(self):
        """Test valid positive float amount."""
        is_valid, error = validate_amount(1500.50)
        assert is_valid is True
        assert error == ""

    def test_valid_small_amount(self):
        """Test valid small positive amount."""
        is_valid, error = validate_amount(0.01)
        assert is_valid is True
        assert error == ""

    def test_valid_large_amount(self):
        """Test valid large amount."""
        is_valid, error = validate_amount(1000000.99)
        assert is_valid is True
        assert error == ""

    def test_zero_amount(self):
        """Test zero amount is invalid."""
        is_valid, error = validate_amount(0)
        assert is_valid is False
        assert "positive" in error.lower()

    def test_negative_amount(self):
        """Test negative amount is invalid."""
        is_valid, error = validate_amount(-100.50)
        assert is_valid is False
        assert "positive" in error.lower()

    def test_none_amount(self):
        """Test None amount."""
        is_valid, error = validate_amount(None)
        assert is_valid is False
        assert "required" in error.lower()

    def test_string_amount(self):
        """Test string amount is invalid."""
        is_valid, error = validate_amount("1000")
        assert is_valid is False
        assert "number" in error.lower()


class TestValidateDateRange:
    """Tests for validate_date_range function."""

    def test_valid_date_range_same_day(self):
        """Test valid date range on same day."""
        date_from = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        date_to = datetime(2024, 1, 1, 15, 0, 0, tzinfo=timezone.utc)
        is_valid, error = validate_date_range(date_from, date_to)
        assert is_valid is True
        assert error == ""

    def test_valid_date_range_multiple_days(self):
        """Test valid date range spanning multiple days."""
        date_from = datetime(2024, 1, 1, tzinfo=timezone.utc)
        date_to = datetime(2024, 1, 10, tzinfo=timezone.utc)
        is_valid, error = validate_date_range(date_from, date_to)
        assert is_valid is True
        assert error == ""

    def test_valid_date_range_equal(self):
        """Test valid date range where dates are equal."""
        date = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        is_valid, error = validate_date_range(date, date)
        assert is_valid is True
        assert error == ""

    def test_invalid_date_range_reversed(self):
        """Test invalid date range where end is before start."""
        date_from = datetime(2024, 1, 10, tzinfo=timezone.utc)
        date_to = datetime(2024, 1, 1, tzinfo=timezone.utc)
        is_valid, error = validate_date_range(date_from, date_to)
        assert is_valid is False
        assert "greater than or equal" in error.lower()

    def test_none_date_from(self):
        """Test None start date."""
        date_to = datetime(2024, 1, 10, tzinfo=timezone.utc)
        is_valid, error = validate_date_range(None, date_to)
        assert is_valid is False
        assert "start date" in error.lower()
        assert "required" in error.lower()

    def test_none_date_to(self):
        """Test None end date."""
        date_from = datetime(2024, 1, 1, tzinfo=timezone.utc)
        is_valid, error = validate_date_range(date_from, None)
        assert is_valid is False
        assert "end date" in error.lower()
        assert "required" in error.lower()

    def test_invalid_type_date_from(self):
        """Test invalid type for start date."""
        date_to = datetime(2024, 1, 10, tzinfo=timezone.utc)
        is_valid, error = validate_date_range("2024-01-01", date_to)
        assert is_valid is False
        assert "datetime object" in error.lower()

    def test_invalid_type_date_to(self):
        """Test invalid type for end date."""
        date_from = datetime(2024, 1, 1, tzinfo=timezone.utc)
        is_valid, error = validate_date_range(date_from, "2024-01-10")
        assert is_valid is False
        assert "datetime object" in error.lower()


class TestValidateNarrativeLength:
    """Tests for validate_narrative_length function."""

    def test_valid_short_narrative(self):
        """Test valid short narrative."""
        narrative = "This is a short narrative."
        is_valid, error = validate_narrative_length(narrative)
        assert is_valid is True
        assert error == ""

    def test_valid_empty_narrative(self):
        """Test valid empty narrative."""
        is_valid, error = validate_narrative_length("")
        assert is_valid is True
        assert error == ""

    def test_valid_max_length_narrative(self):
        """Test valid narrative at exactly 10,000 characters."""
        narrative = "x" * 10000
        is_valid, error = validate_narrative_length(narrative)
        assert is_valid is True
        assert error == ""

    def test_valid_long_narrative(self):
        """Test valid long narrative under limit."""
        narrative = "This is a test narrative. " * 300  # ~7800 chars
        is_valid, error = validate_narrative_length(narrative)
        assert is_valid is True
        assert error == ""

    def test_invalid_too_long_narrative(self):
        """Test invalid narrative exceeding 10,000 characters."""
        narrative = "x" * 10001
        is_valid, error = validate_narrative_length(narrative)
        assert is_valid is False
        assert "exceeds maximum length" in error.lower()
        assert "10001" in error

    def test_invalid_much_too_long_narrative(self):
        """Test invalid narrative far exceeding limit."""
        narrative = "x" * 20000
        is_valid, error = validate_narrative_length(narrative)
        assert is_valid is False
        assert "exceeds maximum length" in error.lower()
        assert "20000" in error

    def test_none_narrative(self):
        """Test None narrative."""
        is_valid, error = validate_narrative_length(None)
        assert is_valid is False
        assert "required" in error.lower()

    def test_invalid_type_narrative(self):
        """Test invalid type for narrative."""
        is_valid, error = validate_narrative_length(12345)
        assert is_valid is False
        assert "string" in error.lower()


class TestValidateActivityTypes:
    """Tests for validate_activity_types function."""

    def test_valid_single_activity_type(self):
        """Test valid single activity type."""
        is_valid, error = validate_activity_types(["Money Laundering"])
        assert is_valid is True
        assert error == ""

    def test_valid_multiple_activity_types(self):
        """Test valid multiple activity types."""
        is_valid, error = validate_activity_types(["Structuring", "Money Laundering", "Fraud"])
        assert is_valid is True
        assert error == ""

    def test_invalid_empty_list(self):
        """Test invalid empty list."""
        is_valid, error = validate_activity_types([])
        assert is_valid is False
        assert "at least one" in error.lower()

    def test_invalid_list_with_empty_strings(self):
        """Test invalid list containing only empty strings."""
        is_valid, error = validate_activity_types(["", "  ", ""])
        assert is_valid is False
        assert "at least one non-empty" in error.lower()

    def test_valid_list_with_some_empty_strings(self):
        """Test valid list with some empty strings but at least one valid."""
        is_valid, error = validate_activity_types(["", "Money Laundering", "  "])
        assert is_valid is True
        assert error == ""

    def test_none_activity_types(self):
        """Test None activity types."""
        is_valid, error = validate_activity_types(None)
        assert is_valid is False
        assert "required" in error.lower()

    def test_invalid_type_not_list(self):
        """Test invalid type (not a list)."""
        is_valid, error = validate_activity_types("Money Laundering")
        assert is_valid is False
        assert "list" in error.lower()

    def test_invalid_list_with_non_string_elements(self):
        """Test list with non-string elements."""
        is_valid, error = validate_activity_types(["Money Laundering", 123, None])
        assert is_valid is True  # Should still pass as long as there's one valid string
        assert error == ""

    def test_invalid_list_with_only_non_string_elements(self):
        """Test list with only non-string elements."""
        is_valid, error = validate_activity_types([123, None, 456])
        assert is_valid is False
        assert "at least one non-empty" in error.lower()


class TestValidationProperties:
    """Property-style tests for SAR validation invariants."""

    def test_property_10_tin_validation(self):
        valid = ["12-3456789", "99-0000001"]
        invalid = ["", "123456789", "12-345678", "1A-3456789"]
        for tin in valid:
            ok, _ = validate_tin(tin)
            assert ok is True
        for tin in invalid:
            ok, _ = validate_tin(tin)
            assert ok is False

    def test_property_11_amount_validation(self):
        for amount in [0.01, 1, 5000.55]:
            ok, _ = validate_amount(amount)
            assert ok is True
        for amount in [0, -1, None, "1.0"]:
            ok, _ = validate_amount(amount)  # type: ignore[arg-type]
            assert ok is False

    def test_property_12_date_range_validation(self):
        now = datetime.now(timezone.utc)
        ok, _ = validate_date_range(now, now + timedelta(days=1))
        assert ok is True
        ok, _ = validate_date_range(now + timedelta(days=1), now)
        assert ok is False

    def test_property_13_narrative_length_validation(self):
        ok, _ = validate_narrative_length("x" * 10000)
        assert ok is True
        ok, _ = validate_narrative_length("x" * 10001)
        assert ok is False

    def test_property_14_activity_type_validation(self):
        ok, _ = validate_activity_types(["Money Laundering"])
        assert ok is True
        ok, _ = validate_activity_types([])
        assert ok is False
