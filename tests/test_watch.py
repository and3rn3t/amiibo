"""Tests for watch mode."""

from __future__ import annotations

import tempfile
import time
from pathlib import Path

import pytest

from amiibo_flipper.watch import WatchStats, _ConversionHandler


def _make_test_bin(size: int = 540) -> bytes:
    """Create a test binary file."""
    if size == 540:
        return b"TEST_BIN" + b"\x00" * 532
    return b"\x00" * size


def test_watch_stats_initialization() -> None:
    """Test WatchStats initialization."""
    stats = WatchStats()
    assert stats.files_converted == 0
    assert stats.files_skipped == 0
    assert stats.errors == 0
    assert stats.session_duration == 0.0


def test_conversion_handler_initialization() -> None:
    """Test ConversionHandler initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        output_dir = tmpdir_path / "output"

        def dummy_convert(**kwargs):
            return {"success": True}

        handler = _ConversionHandler(
            source_dir=tmpdir_path,
            output_dir=output_dir,
            convert_func=dummy_convert,
        )

        assert handler.stats.files_converted == 0
        assert len(handler._processing) == 0


def test_watch_stats_updates() -> None:
    """Test that WatchStats can be updated."""
    stats = WatchStats()
    stats.files_converted = 5
    stats.files_skipped = 2
    stats.errors = 1
    stats.session_duration = 10.5

    assert stats.files_converted == 5
    assert stats.files_skipped == 2
    assert stats.errors == 1
    assert stats.session_duration == 10.5
