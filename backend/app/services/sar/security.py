"""
SAR security utilities.

This module provides security functions for SAR generation including
input sanitization, path validation, and audit logging.
"""

import re
from typing import Optional
from pathlib import Path

from app.utils.logger import get_logger

logger = get_logger(__name__)


def sanitize_text_input(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize text input to prevent injection attacks.
    
    Removes or escapes potentially dangerous characters while preserving
    readability for PDF rendering.
    
    Args:
        text: Input text to sanitize
        max_length: Optional maximum length to truncate to
        
    Returns:
        Sanitized text string safe for PDF rendering
        
    Validates: Requirements 8.6
    """
    if not text:
        return ""
    
    # Convert to string if not already
    text = str(text)
    
    # Remove null bytes
    text = text.replace("\x00", "")
    
    # Remove other control characters except newlines, tabs, and carriage returns
    text = re.sub(r"[\x01-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)
    
    # Escape backslashes to prevent escape sequence injection
    text = text.replace("\\", "\\\\")
    
    # Remove any PDF-specific control sequences
    # Remove form feed, vertical tab
    text = text.replace("\f", "").replace("\v", "")
    
    # Truncate if max_length specified
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    return text


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal and injection.
    
    Args:
        filename: Input filename
        
    Returns:
        Sanitized filename safe for file operations
        
    Validates: Requirements 8.5
    """
    if not filename:
        return "unnamed"
    
    # Remove path separators
    filename = filename.replace("/", "_").replace("\\", "_")
    
    # Remove parent directory references
    filename = filename.replace("..", "_")
    
    # Remove null bytes
    filename = filename.replace("\x00", "")
    
    # Keep only alphanumeric, dash, underscore, and dot
    filename = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)
    
    # Ensure filename doesn't start with dot (hidden file)
    if filename.startswith("."):
        filename = "_" + filename[1:]
    
    # Limit length
    if len(filename) > 255:
        filename = filename[:255]
    
    return filename or "unnamed"


def validate_path_traversal(file_path: str, allowed_base: Path) -> bool:
    """
    Validate file path to prevent path traversal attacks.
    
    Ensures the resolved path is within the allowed base directory.
    
    Args:
        file_path: File path to validate
        allowed_base: Base directory that path must be within
        
    Returns:
        True if path is safe, False if path traversal detected
        
    Validates: Requirements 8.5
    """
    if not file_path:
        logger.warning("Empty file path provided for validation")
        return False
    
    try:
        # Convert to Path objects
        path = Path(file_path)
        base = Path(allowed_base)
        
        # Resolve to absolute paths
        resolved_path = path.resolve()
        resolved_base = base.resolve()
        
        # Check if resolved path is within base directory
        try:
            resolved_path.relative_to(resolved_base)
            return True
        except ValueError:
            # Path is not relative to base (outside allowed directory)
            logger.warning(
                f"Path traversal attempt detected: {file_path} "
                f"is outside {allowed_base}"
            )
            return False
            
    except (ValueError, OSError) as e:
        logger.warning(f"Path validation error for {file_path}: {e}")
        return False


def log_sar_access(
    action: str,
    sar_id: Optional[str] = None,
    report_id: Optional[str] = None,
    user_id: Optional[str] = None,
    success: bool = True,
    error_message: Optional[str] = None
) -> None:
    """
    Log SAR access events for audit trail.
    
    Records all SAR generation, access, and download events with
    relevant metadata for compliance auditing.
    
    Args:
        action: Action performed (e.g., "generate", "download", "access")
        sar_id: Optional SAR record ID
        report_id: Optional report ID
        user_id: Optional user ID performing the action
        success: Whether the action succeeded
        error_message: Optional error message if action failed
        
    Validates: Requirements 8.3, 8.4
    """
    log_data = {
        "action": action,
        "sar_id": sar_id,
        "report_id": report_id,
        "user_id": user_id,
        "success": success,
    }
    
    if error_message:
        log_data["error"] = error_message
    
    # Format log message
    log_parts = [f"SAR_AUDIT: action={action}"]
    
    if sar_id:
        log_parts.append(f"sar_id={sar_id}")
    if report_id:
        log_parts.append(f"report_id={report_id}")
    if user_id:
        log_parts.append(f"user_id={user_id}")
    
    log_parts.append(f"success={success}")
    
    if error_message:
        log_parts.append(f"error={error_message}")
    
    log_message = " ".join(log_parts)
    
    # Log at appropriate level
    if success:
        logger.info(log_message)
    else:
        logger.warning(log_message)


def sanitize_sar_data_for_pdf(sar_data: dict) -> dict:
    """
    Sanitize all text fields in SAR data before PDF generation.
    
    Applies sanitization to all string fields to prevent injection attacks
    in the PDF rendering process.
    
    Args:
        sar_data: Dictionary containing SAR data
        
    Returns:
        Dictionary with sanitized text fields
        
    Validates: Requirements 8.6
    """
    sanitized = {}
    
    for key, value in sar_data.items():
        if isinstance(value, str):
            # Sanitize string fields
            sanitized[key] = sanitize_text_input(value)
        elif isinstance(value, dict):
            # Recursively sanitize nested dictionaries
            sanitized[key] = sanitize_sar_data_for_pdf(value)
        elif isinstance(value, list):
            # Sanitize list items
            sanitized[key] = [
                sanitize_text_input(item) if isinstance(item, str) else item
                for item in value
            ]
        else:
            # Keep non-string values as-is
            sanitized[key] = value
    
    return sanitized
