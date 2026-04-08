"""
SAR data validation functions.

This module provides validation functions for SAR (Suspicious Activity Report) data
to ensure compliance with FinCEN requirements before PDF generation.
"""

import re
from datetime import datetime
from typing import Any, List, Tuple

from app.schemas.sar import SARReportLayout, validate_sar_layout


def validate_tin(tin: str) -> Tuple[bool, str]:
    """
    Validate Tax Identification Number (TIN) follows valid EIN format.
    
    Args:
        tin: Tax Identification Number string
        
    Returns:
        Tuple of (is_valid, error_message)
        - (True, "") if valid
        - (False, error_message) if invalid
        
    Validates: Requirements 4.1
    
    EIN format: XX-XXXXXXX (two digits, hyphen, seven digits)
    """
    if not tin:
        return False, "TIN is required"
    
    pattern = r"^\d{2}-\d{7}$"
    if not re.match(pattern, tin):
        return False, "TIN must follow EIN format: XX-XXXXXXX"
    
    return True, ""


def validate_amount(amount: float) -> Tuple[bool, str]:
    """
    Validate that amount is a positive number.
    
    Args:
        amount: Total amount value
        
    Returns:
        Tuple of (is_valid, error_message)
        - (True, "") if valid
        - (False, error_message) if invalid
        
    Validates: Requirements 4.2
    """
    if amount is None:
        return False, "Amount is required"
    
    if not isinstance(amount, (int, float)):
        return False, "Amount must be a number"
    
    if amount <= 0:
        return False, "Amount must be a positive number"
    
    return True, ""


def validate_date_range(date_from: datetime, date_to: datetime) -> Tuple[bool, str]:
    """
    Validate that activity_date_to is greater than or equal to activity_date_from.
    
    Args:
        date_from: Activity start date
        date_to: Activity end date
        
    Returns:
        Tuple of (is_valid, error_message)
        - (True, "") if valid
        - (False, error_message) if invalid
        
    Validates: Requirements 4.3
    """
    if date_from is None:
        return False, "Activity start date is required"
    
    if date_to is None:
        return False, "Activity end date is required"
    
    if not isinstance(date_from, datetime):
        return False, "Activity start date must be a datetime object"
    
    if not isinstance(date_to, datetime):
        return False, "Activity end date must be a datetime object"
    
    if date_to < date_from:
        return False, "Activity end date must be greater than or equal to start date"
    
    return True, ""


def validate_narrative_length(narrative: str) -> Tuple[bool, str]:
    """
    Validate that narrative does not exceed 10,000 characters.
    
    Args:
        narrative: Narrative text content
        
    Returns:
        Tuple of (is_valid, error_message)
        - (True, "") if valid
        - (False, error_message) if invalid
        
    Validates: Requirements 4.4
    """
    if narrative is None:
        return False, "Narrative is required"
    
    if not isinstance(narrative, str):
        return False, "Narrative must be a string"
    
    if len(narrative) > 10000:
        return False, f"Narrative exceeds maximum length of 10,000 characters (current: {len(narrative)})"
    
    return True, ""


def validate_activity_types(activity_types: List[str]) -> Tuple[bool, str]:
    """
    Validate that at least one activity type is selected.
    
    Args:
        activity_types: List of activity type strings
        
    Returns:
        Tuple of (is_valid, error_message)
        - (True, "") if valid
        - (False, error_message) if invalid
        
    Validates: Requirements 4.5
    """
    if activity_types is None:
        return False, "Activity types are required"
    
    if not isinstance(activity_types, list):
        return False, "Activity types must be a list"
    
    if len(activity_types) == 0:
        return False, "At least one activity type must be selected"
    
    # Filter out empty strings
    non_empty_types = [t for t in activity_types if t and isinstance(t, str) and t.strip()]
    
    if len(non_empty_types) == 0:
        return False, "At least one non-empty activity type must be selected"
    
    return True, ""


def validate_sar_layout_payload(payload: dict[str, Any]) -> tuple[bool, SARReportLayout | None, list[dict[str, Any]]]:
    """
    Validate full SAR layout payload and return structured validation errors.

    Returns:
        (is_valid, layout_or_none, errors)
    """
    layout, errors = validate_sar_layout(payload)
    return len(errors) == 0, layout, errors
