"""Tests for parallel processing."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from amiibo_flipper.parallel import ConversionJob, ParallelResult, convert_files_parallel


def _make_valid_bin() -> bytes:
    """Create valid 540-byte bin file."""
    return b"TEST_BIN" + b"\x00" * 532


def test_parallel_result_initialization() -> None:
    """Test ParallelResult initialization."""
    result = ParallelResult(
        total=10,
        succeeded=8,
        failed=1,
        skipped=1,
        errors=[],
    )
    assert result.total == 10
    assert result.succeeded == 8
    assert result.failed == 1
    assert result.skipped == 1
    assert len(result.errors) == 0


def test_empty_job_list() -> None:
    """Test parallel conversion with empty job list."""
    result = convert_files_parallel([])
    assert result.total == 0
    assert result.succeeded == 0
    assert result.failed == 0


def test_single_conversion_job() -> None:
    """Test parallel conversion with single job."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        source = tmpdir_path / "test.bin"
        output = tmpdir_path / "output" / "test.nfc"

        source.write_bytes(_make_valid_bin())

        jobs = [ConversionJob(source_file=source, output_file=output)]
        result = convert_files_parallel(jobs)

        assert result.total == 1
        assert result.succeeded == 1
        assert result.failed == 0
        assert output.exists()


def test_multiple_jobs() -> None:
    """Test parallel conversion with multiple jobs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        jobs = []

        # Create 5 test files
        for i in range(5):
            source = tmpdir_path / f"test{i}.bin"
            output = tmpdir_path / "output" / f"test{i}.nfc"
            source.write_bytes(_make_valid_bin())
            jobs.append(ConversionJob(source_file=source, output_file=output))

        result = convert_files_parallel(jobs, max_workers=2)

        assert result.total == 5
        assert result.succeeded == 5
        assert result.failed == 0


def test_invalid_file_size() -> None:
    """Test parallel conversion with invalid file size."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        source = tmpdir_path / "invalid.bin"
        output = tmpdir_path / "output" / "invalid.nfc"

        # Write invalid size (not 540 bytes)
        source.write_bytes(b"SHORT")

        jobs = [ConversionJob(source_file=source, output_file=output)]
        result = convert_files_parallel(jobs)

        assert result.total == 1
        assert result.succeeded == 0
        assert result.failed == 1


def test_skip_existing_files() -> None:
    """Test that existing files are skipped when overwrite=False."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        source = tmpdir_path / "test.bin"
        output = tmpdir_path / "output" / "test.nfc"

        source.write_bytes(_make_valid_bin())
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("existing content")

        jobs = [ConversionJob(source_file=source, output_file=output, overwrite=False)]
        result = convert_files_parallel(jobs)

        assert result.total == 1
        assert result.skipped == 1
        assert result.succeeded == 0


def test_overwrite_existing_files() -> None:
    """Test that existing files are overwritten when overwrite=True."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        source = tmpdir_path / "test.bin"
        output = tmpdir_path / "output" / "test.nfc"

        source.write_bytes(_make_valid_bin())
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("existing content")

        jobs = [ConversionJob(source_file=source, output_file=output, overwrite=True)]
        result = convert_files_parallel(jobs)

        assert result.total == 1
        assert result.succeeded == 1
