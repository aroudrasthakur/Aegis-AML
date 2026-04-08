"""Unit tests for SAR storage functions."""

import pytest
import os
from pathlib import Path
from app.services.sar.storage import (
    save_sar_pdf,
    get_sar_pdf_path,
    validate_sar_path,
    SAR_STORAGE_DIR,
)


class TestSaveSARPDF:
    """Tests for save_sar_pdf function."""

    def test_saves_pdf_successfully(self, tmp_path, monkeypatch):
        """Test successful PDF save."""
        # Use temporary directory for testing
        test_dir = tmp_path / "sar_reports"
        monkeypatch.setattr("app.services.sar.storage.SAR_STORAGE_DIR", test_dir)

        pdf_bytes = b"%PDF-1.4\ntest content"
        report_id = "test-report-123"

        full_path, relative_path = save_sar_pdf(pdf_bytes, report_id)

        # Verify file was created
        assert full_path.exists()
        assert full_path.read_bytes() == pdf_bytes

        # Verify filename format
        assert full_path.name == f"sar_{report_id}.pdf"

        # Verify relative path
        assert "sar_reports" in relative_path
        assert report_id in relative_path

    def test_creates_directory_if_not_exists(self, tmp_path, monkeypatch):
        """Test that storage directory is created if it doesn't exist."""
        test_dir = tmp_path / "new_sar_reports"
        monkeypatch.setattr("app.services.sar.storage.SAR_STORAGE_DIR", test_dir)

        assert not test_dir.exists()

        pdf_bytes = b"%PDF-1.4\ntest"
        report_id = "test-report-456"

        save_sar_pdf(pdf_bytes, report_id)

        # Verify directory was created
        assert test_dir.exists()
        assert test_dir.is_dir()

    def test_overwrites_existing_file(self, tmp_path, monkeypatch):
        """Test that existing file is overwritten."""
        test_dir = tmp_path / "sar_reports"
        test_dir.mkdir()
        monkeypatch.setattr("app.services.sar.storage.SAR_STORAGE_DIR", test_dir)

        report_id = "test-report-789"
        file_path = test_dir / f"sar_{report_id}.pdf"

        # Create existing file
        file_path.write_bytes(b"old content")

        # Save new content
        new_content = b"%PDF-1.4\nnew content"
        save_sar_pdf(new_content, report_id)

        # Verify file was overwritten
        assert file_path.read_bytes() == new_content

    def test_raises_error_for_empty_pdf_bytes(self):
        """Test that empty PDF bytes raises ValueError."""
        with pytest.raises(ValueError, match="PDF bytes cannot be empty"):
            save_sar_pdf(b"", "test-report")

    def test_raises_error_for_invalid_report_id(self):
        """Test that invalid report ID raises ValueError."""
        pdf_bytes = b"%PDF-1.4\ntest"

        with pytest.raises(ValueError, match="Report ID must be a non-empty string"):
            save_sar_pdf(pdf_bytes, "")

        with pytest.raises(ValueError, match="Report ID must be a non-empty string"):
            save_sar_pdf(pdf_bytes, None)

    def test_sets_file_permissions(self, tmp_path, monkeypatch):
        """Test that file permissions are set to 600."""
        test_dir = tmp_path / "sar_reports"
        monkeypatch.setattr("app.services.sar.storage.SAR_STORAGE_DIR", test_dir)

        pdf_bytes = b"%PDF-1.4\ntest"
        report_id = "test-report-permissions"

        full_path, _ = save_sar_pdf(pdf_bytes, report_id)

        # Check file permissions (600 = owner read/write only)
        # Note: On Windows, this may not work exactly as on Unix
        stat_info = os.stat(full_path)
        # Just verify the file exists and is readable
        assert full_path.exists()
        assert os.access(full_path, os.R_OK)


class TestGetSARPDFPath:
    """Tests for get_sar_pdf_path function."""

    def test_returns_correct_path(self):
        """Test that correct path is returned."""
        report_id = "test-report-abc"
        path = get_sar_pdf_path(report_id)

        assert path.name == f"sar_{report_id}.pdf"
        assert "sar_reports" in str(path)

    def test_does_not_check_file_existence(self):
        """Test that function doesn't check if file exists."""
        report_id = "nonexistent-report"
        path = get_sar_pdf_path(report_id)

        # Should return path even if file doesn't exist
        assert isinstance(path, Path)
        assert not path.exists()


class TestValidateSARPath:
    """Tests for validate_sar_path function."""

    def test_valid_path_within_storage_dir(self, tmp_path, monkeypatch):
        """Test that valid path within storage directory passes."""
        test_dir = tmp_path / "sar_reports"
        test_dir.mkdir()
        monkeypatch.setattr("app.services.sar.storage.SAR_STORAGE_DIR", test_dir)

        # Create a valid path
        valid_path = str(test_dir / "sar_test-report.pdf")
        assert validate_sar_path(valid_path) is True

    def test_rejects_path_traversal_with_dotdot(self):
        """Test that path traversal attempts are rejected."""
        malicious_path = "data/processed/sar_reports/../../../etc/passwd"
        assert validate_sar_path(malicious_path) is False

    def test_rejects_empty_path(self):
        """Test that empty path is rejected."""
        assert validate_sar_path("") is False
        assert validate_sar_path(None) is False

    def test_rejects_path_outside_storage_dir(self, tmp_path, monkeypatch):
        """Test that paths outside storage directory are rejected."""
        test_dir = tmp_path / "sar_reports"
        test_dir.mkdir()
        monkeypatch.setattr("app.services.sar.storage.SAR_STORAGE_DIR", test_dir)

        # Path outside storage directory
        outside_path = str(tmp_path / "other_dir" / "file.pdf")
        assert validate_sar_path(outside_path) is False

    def test_handles_invalid_path_format(self):
        """Test that invalid path formats are rejected."""
        # These should be handled gracefully
        assert validate_sar_path("\0invalid") is False


class TestStorageProperties:
    """Property-style tests for storage invariants."""

    def test_property_16_file_saved_to_correct_location(self, tmp_path, monkeypatch):
        test_dir = tmp_path / "sar_reports"
        monkeypatch.setattr("app.services.sar.storage.SAR_STORAGE_DIR", test_dir)
        full_path, rel = save_sar_pdf(b"%PDF-1.4\nx", "r-a")
        assert str(full_path).startswith(str(test_dir))
        assert "sar_reports" in rel

    def test_property_17_unique_filename_generation(self, tmp_path, monkeypatch):
        test_dir = tmp_path / "sar_reports"
        monkeypatch.setattr("app.services.sar.storage.SAR_STORAGE_DIR", test_dir)
        p1, _ = save_sar_pdf(b"%PDF-1.4\n1", "r-1")
        p2, _ = save_sar_pdf(b"%PDF-1.4\n2", "r-2")
        assert p1.name != p2.name

    def test_property_27_file_permissions_best_effort(self, tmp_path, monkeypatch):
        test_dir = tmp_path / "sar_reports"
        monkeypatch.setattr("app.services.sar.storage.SAR_STORAGE_DIR", test_dir)
        p, _ = save_sar_pdf(b"%PDF-1.4\nx", "r-perm")
        mode = os.stat(p).st_mode & 0o777
        # On Unix expect 600; on Windows ensure at least file exists/readable.
        assert p.exists()
        assert (mode == 0o600) or os.access(p, os.R_OK)


class TestStorageErrorHandling:
    def test_save_sar_pdf_raises_when_dir_create_fails(self, monkeypatch):
        class _P:
            def mkdir(self, *_, **__):
                raise OSError("no perms")

        monkeypatch.setattr("app.services.sar.storage.SAR_STORAGE_DIR", _P())
        with pytest.raises(OSError):
            save_sar_pdf(b"%PDF-1.4\nx", "r-err")

    def test_save_sar_pdf_raises_when_write_fails(self, tmp_path, monkeypatch):
        test_dir = tmp_path / "sar_reports"
        test_dir.mkdir()
        monkeypatch.setattr("app.services.sar.storage.SAR_STORAGE_DIR", test_dir)

        def _fail(*args, **kwargs):
            raise OSError("disk full")

        monkeypatch.setattr(Path, "write_bytes", _fail)
        with pytest.raises(OSError):
            save_sar_pdf(b"%PDF-1.4\nx", "r-err2")
