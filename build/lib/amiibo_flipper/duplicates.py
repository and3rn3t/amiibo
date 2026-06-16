"""Duplicate detection for amiibo files."""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path


logger = logging.getLogger(__name__)


@dataclass
class DuplicateInfo:
    """Information about duplicate files."""

    file_path: Path
    content_hash: str
    other_files: list[Path]  # Other files with same hash


@dataclass
class DuplicateScanResult:
    """Results from scanning for duplicates."""

    total_files: int
    duplicates_found: int
    duplicate_groups: list[list[Path]]
    hashes: dict[str, list[Path]]  # content_hash -> [file_paths]


def scan_for_duplicates(directory: Path) -> DuplicateScanResult:
    """Scan directory for duplicate NFC/BIN files by content hash."""
    hashes: dict[str, list[Path]] = {}
    total = 0

    for file_path in directory.rglob("*"):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in [".nfc", ".bin"]:
            continue

        total += 1
        content_hash = _hash_file(file_path)
        if content_hash not in hashes:
            hashes[content_hash] = []
        hashes[content_hash].append(file_path)

    # Find duplicate groups (multiple files with same hash)
    duplicate_groups = [paths for paths in hashes.values() if len(paths) > 1]
    duplicates_found = sum(len(group) - 1 for group in duplicate_groups)

    logger.debug(f"Scanned {total} files, found {duplicates_found} duplicates")

    return DuplicateScanResult(
        total_files=total,
        duplicates_found=duplicates_found,
        duplicate_groups=duplicate_groups,
        hashes=hashes,
    )


def _hash_file(path: Path, chunk_size: int = 65536) -> str:
    """Compute SHA256 hash of file content."""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()[:16]  # Use first 16 chars for brevity


def save_duplication_report(result: DuplicateScanResult, output_path: Path) -> None:
    """Save duplicate scan results to a JSON report."""
    report = {
        "total_files": result.total_files,
        "duplicates_found": result.duplicates_found,
        "duplicate_groups": [
            [str(p) for p in group] for group in result.duplicate_groups
        ],
    }
    output_path.write_text(json.dumps(report, indent=2))
    logger.info(f"Saved duplicate report to {output_path}")


def format_duplicates_for_display(result: DuplicateScanResult) -> str:
    """Format duplicate scan results as human-readable text."""
    if not result.duplicate_groups:
        return f"✓ No duplicates found ({result.total_files} files scanned)"

    lines = [
        f"⚠ Found {result.duplicates_found} duplicate files in {result.duplicate_groups.__len__()} groups:",
        "",
    ]

    for i, group in enumerate(result.duplicate_groups, 1):
        lines.append(f"  Group {i} ({len(group)} files):")
        for file_path in sorted(group):
            lines.append(f"    - {file_path}")
        lines.append("")

    return "\n".join(lines)
