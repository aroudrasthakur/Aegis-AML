"""
SAR configuration module.

This module provides configuration management for SAR generation,
including filing institution information.
"""

import os
from typing import Optional

from app.schemas.sar import FilingInstitution
from app.utils.logger import get_logger

logger = get_logger(__name__)


def get_filing_institution_config() -> FilingInstitution:
    """
    Get filing institution information from configuration.
    
    Loads filing institution details from environment variables with
    sensible defaults for development/testing.
    
    Returns:
        FilingInstitution object with institution details
        
    Environment Variables:
        FILING_INSTITUTION_NAME: Institution name
        FILING_INSTITUTION_TIN: Tax Identification Number (EIN format)
        FILING_INSTITUTION_ADDRESS: Street address
        FILING_INSTITUTION_CITY: City
        FILING_INSTITUTION_STATE: State (2-letter code)
        FILING_INSTITUTION_ZIP: ZIP code
        FILING_INSTITUTION_CONTACT_NAME: Contact person name
        FILING_INSTITUTION_CONTACT_PHONE: Contact phone number
        FILING_INSTITUTION_CONTACT_EMAIL: Contact email address
        
    Validates: Requirements 2.1, Configuration Requirements section
    """
    filing_institution = FilingInstitution(
        name=os.getenv("FILING_INSTITUTION_NAME", "AML Compliance Institution"),
        tin=os.getenv("FILING_INSTITUTION_TIN", "12-3456789"),
        address=os.getenv("FILING_INSTITUTION_ADDRESS", "123 Main Street"),
        city=os.getenv("FILING_INSTITUTION_CITY", "New York"),
        state=os.getenv("FILING_INSTITUTION_STATE", "NY"),
        zip_code=os.getenv("FILING_INSTITUTION_ZIP", "10001"),
        contact_name=os.getenv("FILING_INSTITUTION_CONTACT_NAME", "Compliance Officer"),
        contact_phone=os.getenv("FILING_INSTITUTION_CONTACT_PHONE", "555-0100"),
        contact_email=os.getenv("FILING_INSTITUTION_CONTACT_EMAIL", "compliance@example.com"),
    )
    
    logger.debug(f"Retrieved filing institution config: {filing_institution.name}")
    return filing_institution


def validate_filing_institution_config(config: Optional[FilingInstitution] = None) -> tuple[bool, list[str]]:
    """
    Validate filing institution configuration.
    
    Checks that all required fields are present and properly formatted.
    
    Args:
        config: FilingInstitution object to validate, or None to validate current config
        
    Returns:
        Tuple of (is_valid, error_messages)
        - is_valid: True if configuration is valid
        - error_messages: List of validation error messages (empty if valid)
        
    Validates: Requirements 4.1, Configuration Requirements section
    """
    if config is None:
        config = get_filing_institution_config()
    
    errors = []
    
    # Check required fields are non-empty
    required_fields = {
        "name": config.name,
        "tin": config.tin,
        "address": config.address,
        "city": config.city,
        "state": config.state,
        "zip_code": config.zip_code,
        "contact_name": config.contact_name,
        "contact_phone": config.contact_phone,
        "contact_email": config.contact_email,
    }
    
    for field_name, field_value in required_fields.items():
        if not field_value or not str(field_value).strip():
            errors.append(f"Filing institution {field_name} is required")
    
    # Validate TIN format (XX-XXXXXXX)
    if config.tin:
        from app.services.sar.validation import validate_tin
        is_valid_tin, _ = validate_tin(config.tin)
        if not is_valid_tin:
            errors.append(f"Filing institution TIN has invalid format: {config.tin}")
    
    # Validate state is 2 characters
    if config.state and len(config.state) != 2:
        errors.append(f"Filing institution state must be 2-letter code: {config.state}")
    
    # Validate email format (basic check)
    if config.contact_email and "@" not in config.contact_email:
        errors.append(f"Filing institution contact email is invalid: {config.contact_email}")
    
    is_valid = len(errors) == 0
    
    if not is_valid:
        logger.warning(f"Filing institution config validation failed: {errors}")
    else:
        logger.debug("Filing institution config validation passed")
    
    return is_valid, errors
