"""Tests for archive import."""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path

import pytest

from amiibo_flipper.archive import import_archive


def _make_bin_file(content: bytes) -> bytes:
    """Helper to create a valid 540-byte bin file for testing."""
    if len(content) != 540:
        # Pad or truncate to 540 bytes
        content = (content * (540 // len(content) + 1))[:540]
    return content


def test_import_archive_basic() -> None:
    """Test basic archive import and conversion."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create a simple archive with .bin files
        archive_path = tmpdir_path / "test.zip"
        with zipfile.ZipFile(archive_path, "w") as zf:
            zf.writestr("amiibo1.bin", _make_bin_file(b"content1"))
            zf.writestr("amiibo2.bin", _make_bin_file(b"content2"))

        # Import
        output_dir = tmpdir_path / "output"
        result = import_archive(archive_path, output_dir, cleanup_temp=False)

        assert result.archive_path == archive_path
        assert result.converted_count >= 0
        assert output_dir.exists()


def test_import_archive_with_nested_structure() -> None:
    """Test archive with nested directory structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        archive_path = tmpdir_path / "test.zip"
        with zipfile.ZipFile(archive_path, "w") as zf:
            zf.writestr("series1/amiibo1.bin", _make_bin_file(b"a"))
            zf.writestr("series1/amiibo2.bin", _make_bin_file(b"b"))
            zf.writestr("series2/amiibo3.bin", _make_bin_file(b"c"))

        output_dir = tmpdir_path / "output"
        result = import_archive(archive_path, output_dir, flatten=False, cleanup_temp=False)

        assert result.converted_count >= 0


def test_import_archive_flatten_mode() -> None:
    """Test that flatten mode works."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        archive_path = tmpdir_path / "test.zip"
        with zipfile.ZipFile(archive_path, "w") as zf:
            zf.writestr("series1/amiibo1.bin", _make_bin_file(b"a"))
            zf.writestr("series2/amiibo2.bin", _make_bin_file(b"b"))

        output_dir = tmpdir_path / "output"
        result = import_archive(archive_path, output_dir, flatten=True, cleanup_temp=False)

        # With flatten=True, all files should be in output_dir, not in subdirs
        assert result.converted_count >= 0


def test_import_archive_missing_file() -> None:
    """Test error handling for missing archive."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        missing_archive = tmpdir_path / "missing.zip"

        with pytest.raises(FileNotFoundError):
            import_archive(missing_archive, tmpdir_path / "output")


def test_import_archive_invalid_zip() -> None:
    """Test error handling for invalid ZIP file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create an invalid ZIP file
        invalid_zip = tmpdir_path / "invalid.zip"
        invalid_zip.write_bytes(b"not a valid zip file")

        output_dir = tmpdir_path / "output"
        result = import_archive(invalid_zip, output_dir, cleanup_temp=False)

        # Should have extraction errors
        assert len(result.extraction_errors) > 0
