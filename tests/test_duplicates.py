"""Tests for duplicate detection."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from amiibo_flipper.duplicates import (
    format_duplicates_for_display,
    save_duplication_report,
    scan_for_duplicates,
)


def _make_test_file(path: Path, content: bytes) -> None:
    """Helper to create test file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def test_no_duplicates() -> None:
    """Test scan with no duplicates."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        _make_test_file(tmpdir_path / "file1.nfc", b"content1")
        _make_test_file(tmpdir_path / "file2.nfc", b"content2")

        result = scan_for_duplicates(tmpdir_path)
        assert result.total_files == 2
        assert result.duplicates_found == 0
        assert len(result.duplicate_groups) == 0


def test_finds_duplicates() -> None:
    """Test scan finds duplicate files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        content = b"same content"
        _make_test_file(tmpdir_path / "file1.nfc", content)
        _make_test_file(tmpdir_path / "file2.nfc", content)
        _make_test_file(tmpdir_path / "file3.nfc", b"different")

        result = scan_for_duplicates(tmpdir_path)
        assert result.total_files == 3
        assert result.duplicates_found == 1  # 2 files - 1 = 1 duplicate
        assert len(result.duplicate_groups) == 1
        assert len(result.duplicate_groups[0]) == 2


def test_ignores_non_nfc_files() -> None:
    """Test that only .nfc and .bin files are scanned."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        _make_test_file(tmpdir_path / "file.nfc", b"content")
        _make_test_file(tmpdir_path / "file.txt", b"ignored")
        _make_test_file(tmpdir_path / "file.json", b"ignored")

        result = scan_for_duplicates(tmpdir_path)
        assert result.total_files == 1


def test_case_insensitive_extension() -> None:
    """Test that .NFC and .BIN extensions are detected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        content = b"test"
        _make_test_file(tmpdir_path / "file1.NFC", content)
        _make_test_file(tmpdir_path / "file2.nfc", content)
        _make_test_file(tmpdir_path / "file3.BIN", content)

        result = scan_for_duplicates(tmpdir_path)
        assert result.total_files == 3


def test_format_no_duplicates() -> None:
    """Test formatting with no duplicates."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        _make_test_file(tmpdir_path / "file.nfc", b"content")

        result = scan_for_duplicates(tmpdir_path)
        formatted = format_duplicates_for_display(result)
        assert "No duplicates found" in formatted
        assert "1 files scanned" in formatted


def test_save_duplication_report() -> None:
    """Test saving report to JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        content = b"duplicate"
        _make_test_file(tmpdir_path / "file1.nfc", content)
        _make_test_file(tmpdir_path / "file2.nfc", content)

        result = scan_for_duplicates(tmpdir_path)
        report_path = tmpdir_path / "report.json"
        save_duplication_report(result, report_path)

        assert report_path.exists()
        report_data = json.loads(report_path.read_text())
        assert report_data["total_files"] == 2
        assert report_data["duplicates_found"] == 1
        assert len(report_data["duplicate_groups"]) == 1
