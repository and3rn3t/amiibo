"""Parallel processing utilities for batch conversions."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from amiibo_flipper.converter import bin_to_nfc


logger = logging.getLogger(__name__)


@dataclass
class ConversionJob:
    """A single file conversion job."""

    source_file: Path
    output_file: Path
    overwrite: bool = False


@dataclass
class ParallelResult:
    """Results from parallel conversion."""

    total: int
    succeeded: int
    failed: int
    skipped: int
    errors: list[tuple[Path, str]]  # (file, error_message)


def convert_files_parallel(
    jobs: list[ConversionJob],
    max_workers: int | None = None,
) -> ParallelResult:
    """Convert multiple files in parallel.

    Args:
        jobs: List of ConversionJob items
        max_workers: Number of worker threads (default: CPU count)

    Returns:
        ParallelResult with statistics
    """
    if not jobs:
        return ParallelResult(total=0, succeeded=0, failed=0, skipped=0, errors=[])

    errors: list[tuple[Path, str]] = []
    succeeded = 0
    failed = 0
    skipped = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_convert_single_job, job): job
            for job in jobs
        }

        for future in as_completed(futures):
            job = futures[future]
            try:
                result = future.result()
                if result["status"] == "success":
                    succeeded += 1
                elif result["status"] == "skipped":
                    skipped += 1
                    logger.debug(f"⊘ Skipped: {job.source_file.name}")
                else:
                    failed += 1
                    errors.append((job.source_file, result.get("error", "Unknown error")))
                    logger.warning(f"✗ Failed: {job.source_file.name}")

            except Exception as e:
                failed += 1
                errors.append((job.source_file, str(e)))
                logger.exception(f"Exception converting {job.source_file.name}")

    logger.info(f"Parallel conversion: {succeeded} succeeded, {failed} failed, {skipped} skipped")

    return ParallelResult(
        total=len(jobs),
        succeeded=succeeded,
        failed=failed,
        skipped=skipped,
        errors=errors,
    )


def _convert_single_job(job: ConversionJob) -> dict:
    """Convert a single job (runs in worker thread)."""
    if not job.source_file.exists():
        return {"status": "failed", "error": "Source file not found"}

    if job.output_file.exists() and not job.overwrite:
        return {"status": "skipped", "reason": "File exists"}

    try:
        data = job.source_file.read_bytes()

        if len(data) != 540:
            return {"status": "failed", "error": f"Invalid size: {len(data)} bytes"}

        nfc_content = bin_to_nfc(data)
        job.output_file.parent.mkdir(parents=True, exist_ok=True)
        job.output_file.write_text(nfc_content)

        return {"status": "success"}

    except Exception as e:
        return {"status": "failed", "error": str(e)}
