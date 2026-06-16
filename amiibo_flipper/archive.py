"""Import amiibo files from ZIP archives."""

from __future__ import annotations

import logging
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from amiibo_flipper.converter import convert_directory


logger = logging.getLogger(__name__)


@dataclass
class ArchiveImportResult:
    """Results from importing an archive."""

    archive_path: Path
    extract_dir: Path
    converted_count: int
    skipped_count: int
    extraction_errors: list[str] = field(default_factory=list)


def import_archive(
    archive_path: Path,
    output_dir: Path,
    extract_temp_dir: Path | None = None,
    overwrite: bool = False,
    flatten: bool = False,
    cleanup_temp: bool = True,
) -> ArchiveImportResult:
    """Extract archive and convert NFC/BIN files.

    Args:
        archive_path: Path to ZIP file
        output_dir: Directory to write converted .nfc files
        extract_temp_dir: Temporary directory for extraction (defaults to output_dir/.tmp)
        overwrite: Overwrite existing NFC files
        flatten: Flatten directory structure
        cleanup_temp: Delete temporary extraction directory after conversion

    Returns:
        ArchiveImportResult with conversion statistics
    """
    if not archive_path.exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")

    if extract_temp_dir is None:
        extract_temp_dir = output_dir / ".tmp"

    logger.info(f"Extracting archive: {archive_path}")
    extract_temp_dir.mkdir(parents=True, exist_ok=True)

    errors = _extract_archive_safe(archive_path, extract_temp_dir)

    logger.info(f"Converting NFC/BIN files to {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    conversion_result = convert_directory(
        source_dir=extract_temp_dir,
        output_dir=output_dir,
        overwrite=overwrite,
        flatten=flatten,
    )

    if cleanup_temp:
        import shutil
        logger.debug(f"Cleaning up temporary directory: {extract_temp_dir}")
        shutil.rmtree(extract_temp_dir, ignore_errors=True)

    return ArchiveImportResult(
        archive_path=archive_path,
        extract_dir=output_dir,
        converted_count=conversion_result.converted,
        skipped_count=conversion_result.skipped_existing + conversion_result.skipped_invalid_size,
        extraction_errors=errors,
    )


def _extract_archive_safe(archive_path: Path, target_dir: Path) -> list[str]:
    """Extract ZIP archive with error recovery.

    Returns list of extraction errors encountered.
    """
    errors = []

    try:
        with zipfile.ZipFile(archive_path, "r") as zf:
            for member in zf.namelist():
                try:
                    # Sanitize path to prevent directory traversal
                    target_path = (target_dir / member).resolve()
                    if not str(target_path).startswith(str(target_dir.resolve())):
                        errors.append(f"Skipped suspicious path: {member}")
                        continue

                    # Extract to target
                    if member.endswith("/"):
                        target_path.mkdir(parents=True, exist_ok=True)
                    else:
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        with zf.open(member) as source, open(target_path, "wb") as target:
                            target.write(source.read())

                except Exception as e:
                    errors.append(f"Failed to extract {member}: {e}")

    except zipfile.BadZipFile as e:
        errors.append(f"Invalid ZIP file: {e}")
    except Exception as e:
        errors.append(f"Extraction failed: {e}")

    if errors:
        logger.warning(f"Extraction errors: {len(errors)} items skipped")

    return errors
