"""
SAR file storage utilities.

This module provides functions for saving SAR PDF files to disk with proper
permissions and unique filename generation.
"""

import os
from pathlib import Path
from typing import Tuple

from app.utils.logger import get_logger

logger = get_logger(__name__)

# Default storage directory for SAR PDFs
SAR_STORAGE_DIR = Path("data/processed/sar_reports")


def save_sar_pdf(pdf_bytes: bytes, report_id: str) -> Tuple[Path, str]:
    """
    Save SAR PDF to storage with unique filename and restricted permissions.

    Args:
        pdf_bytes: PDF file content as bytes
        report_id: Report ID to use for filename generation

    Returns:
        Tuple of (full_path, relative_path_str)
        - full_path: Absolute Path object to the saved file
        - relative_path_str: Relative path string for database storage

    Raises:
        OSError: If file cannot be saved due to permissions or disk space
        ValueError: If pdf_bytes is empty or report_id is invalid

    Validates: Requirements 5.1, 5.2, 8.2
    """
    if not pdf_bytes:
        raise ValueError("PDF bytes cannot be empty")

    if not report_id or not isinstance(report_id, str):
        raise ValueError("Report ID must be a non-empty string")

    # Ensure storage directory exists
    try:
        SAR_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured storage directory exists: {SAR_STORAGE_DIR}")
    except OSError as e:
        logger.error(f"Failed to create storage directory: {e}")
        raise OSError(f"Failed to create storage directory: {e}") from e

    # Generate unique filename based on report ID
    filename = f"sar_{report_id}.pdf"
    file_path = SAR_STORAGE_DIR / filename

    # Check if file already exists (should not happen with unique report_id)
    if file_path.exists():
        logger.warning(f"SAR file already exists: {file_path}, will overwrite")

    # Write PDF bytes to file
    try:
        file_path.write_bytes(pdf_bytes)
        logger.info(f"Saved SAR PDF to {file_path} ({len(pdf_bytes)} bytes)")
    except OSError as e:
        logger.error(f"Failed to write SAR PDF file: {e}")
        raise OSError(f"Failed to save SAR PDF: {e}") from e

    # Set file permissions to 600 (read/write for owner only)
    try:
        os.chmod(file_path, 0o600)
        logger.debug(f"Set file permissions to 600 for {file_path}")
    except OSError as e:
        logger.warning(f"Failed to set file permissions: {e}")
        # Don't raise - file is saved, just permissions couldn't be set

    # Return both absolute path and relative path string
    # Try to get relative path, but fall back to absolute if not possible
    try:
        relative_path = str(file_path.relative_to(Path.cwd()))
    except ValueError:
        # File is not relative to cwd (e.g., in temp directory during tests)
        relative_path = str(file_path)
    
    return file_path, relative_path


def get_sar_pdf_path(report_id: str) -> Path:
    """
    Get the expected file path for a SAR PDF by report ID.

    Args:
        report_id: Report ID

    Returns:
        Path object to the expected SAR PDF file

    Note: This does not check if the file exists.
    """
    filename = f"sar_{report_id}.pdf"
    return SAR_STORAGE_DIR / filename


def validate_sar_path(sar_path: str) -> bool:
    """
    Validate SAR file path to prevent path traversal attacks.

    Args:
        sar_path: File path string to validate

    Returns:
        True if path is valid and safe, False otherwise

    Validates: Requirements 8.5
    """
    if not sar_path:
        return False

    # Convert to Path object
    try:
        path = Path(sar_path)
    except (ValueError, TypeError):
        logger.warning(f"Invalid path format: {sar_path}")
        return False

    # Check for path traversal attempts
    if ".." in path.parts:
        logger.warning(f"Path traversal attempt detected: {sar_path}")
        return False

    # Ensure path is within SAR storage directory
    try:
        # Resolve to absolute path and check if it's within storage dir
        abs_path = path.resolve()
        abs_storage = SAR_STORAGE_DIR.resolve()

        # Check if the file path starts with the storage directory path
        if not str(abs_path).startswith(str(abs_storage)):
            logger.warning(f"Path outside storage directory: {sar_path}")
            return False
    except (ValueError, OSError) as e:
        logger.warning(f"Path validation error: {e}")
        return False

    return True
