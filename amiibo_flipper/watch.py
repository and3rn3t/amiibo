"""Watch mode for auto-converting new amiibo files."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    raise ImportError("watchdog package required for watch mode. Install with: pip install watchdog")


logger = logging.getLogger(__name__)


@dataclass
class WatchStats:
    """Statistics from a watch session."""

    files_converted: int = 0
    files_skipped: int = 0
    errors: int = 0
    session_duration: float = 0.0


class _ConversionHandler(FileSystemEventHandler):
    """Handle file system events for auto-conversion."""

    def __init__(
        self,
        source_dir: Path,
        output_dir: Path,
        convert_func,
        flatten: bool = False,
        overwrite: bool = False,
    ):
        self.source_dir = source_dir
        self.output_dir = output_dir
        self.convert_func = convert_func
        self.flatten = flatten
        self.overwrite = overwrite
        self.stats = WatchStats()
        self._processing: set[str] = set()  # Track files being processed

    def on_created(self, event) -> None:
        """Handle file creation."""
        if event.is_directory:
            return

        file_path = Path(str(event.src_path))
        if file_path.suffix.lower() not in [".bin", ".nfc"]:
            return

        # Skip if already processing this file
        if str(file_path) in self._processing:
            return

        self._processing.add(str(file_path))
        try:
            # Wait briefly for file to finish writing
            time.sleep(0.5)

            if not file_path.exists():
                return

            logger.info(f"New file detected: {file_path.name}")
            self._convert_file(file_path)

        finally:
            self._processing.discard(str(file_path))

    def _convert_file(self, file_path: Path) -> None:
        """Convert a single file."""
        try:
            result = self.convert_func(
                source=file_path,
                output_dir=self.output_dir,
                flatten=self.flatten,
                overwrite=self.overwrite,
            )

            if result.get("success"):
                self.stats.files_converted += 1
                logger.info(f"✓ Converted: {file_path.name}")
            else:
                self.stats.files_skipped += 1
                logger.debug(f"⊘ Skipped: {file_path.name} ({result.get('reason', 'unknown')})")

        except Exception:
            self.stats.errors += 1
            logger.exception("Error converting file")


def watch_directory(
    source_dir: Path,
    output_dir: Path,
    convert_func,
    flatten: bool = False,
    overwrite: bool = False,
) -> WatchStats:
    """Watch a directory and auto-convert new amiibo files.

    Args:
        source_dir: Directory to monitor
        output_dir: Directory for converted files
        convert_func: Function to call for conversion (signature: convert_func(source, output_dir, flatten, overwrite))
        flatten: Flatten output directory structure
        overwrite: Overwrite existing files

    Returns:
        WatchStats with session information
    """
    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    handler = _ConversionHandler(
        source_dir=source_dir,
        output_dir=output_dir,
        convert_func=convert_func,
        flatten=flatten,
        overwrite=overwrite,
    )

    observer = Observer()
    observer.schedule(handler, str(source_dir), recursive=True)
    observer.start()

    logger.info(f"👀 Watching for new files in: {source_dir}")
    logger.info(f"📁 Output directory: {output_dir}")
    logger.info("Press Ctrl+C to stop watching...")

    start_time = time.time()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping watch mode...")
    finally:
        observer.stop()
        observer.join()

    handler.stats.session_duration = time.time() - start_time
    return handler.stats
