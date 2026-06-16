"""Batch mode for chaining amiibo-flipper commands."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from amiibo_flipper.client import fetch_amiibos
from amiibo_flipper.converter import convert_directory
from amiibo_flipper.exporter import export_entries
from amiibo_flipper.images import download_images
from amiibo_flipper.inventory import build_inventory, render_inventory_report
from amiibo_flipper.nfc import import_nfc_files


logger = logging.getLogger(__name__)


@dataclass
class BatchCommand:
    """A single command in a batch operation."""

    name: str  # e.g., "fetch", "export", "sync"
    kwargs: dict[str, Any]


@dataclass
class BatchResult:
    """Result from a batch operation."""

    commands_run: int
    commands_succeeded: int
    commands_failed: int
    failures: list[tuple[str, str]]  # (command_name, error_message)
    outputs: dict[str, Any]  # command_name -> output value


class BatchRunner:
    """Execute a sequence of amiibo-flipper commands."""

    def __init__(self):
        self.result = BatchResult(
            commands_run=0,
            commands_succeeded=0,
            commands_failed=0,
            failures=[],
            outputs={},
        )
        self._commands = {
            "fetch": self._batch_fetch,
            "export": self._batch_export,
            "sync": self._batch_sync,
            "convert-bin": self._batch_convert_bin,
            "download-images": self._batch_download_images,
            "inventory": self._batch_inventory,
        }

    def run(self, commands: list[BatchCommand]) -> BatchResult:
        """Execute batch of commands in sequence.

        Args:
            commands: List of BatchCommand items to run

        Returns:
            BatchResult with execution details
        """
        for cmd in commands:
            self.result.commands_run += 1
            logger.info(f"Running batch command [{self.result.commands_run}/{len(commands)}]: {cmd.name}")

            try:
                if cmd.name not in self._commands:
                    raise ValueError(f"Unknown command: {cmd.name}")

                output = self._commands[cmd.name](cmd.kwargs)
                self.result.outputs[cmd.name] = output
                self.result.commands_succeeded += 1
                logger.info(f"✓ {cmd.name} completed")

            except Exception as e:
                self.result.commands_failed += 1
                self.result.failures.append((cmd.name, str(e)))
                logger.exception(f"Command {cmd.name} failed")

        return self.result

    @staticmethod
    def _batch_fetch(kwargs: dict) -> dict:
        """Fetch amiibo data."""
        output_path = Path(kwargs.get("output", "data/amiibo.json"))
        amiibos = fetch_amiibos()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        import json
        from dataclasses import asdict
        payload = {"amiibo": [asdict(item) for item in amiibos]}
        output_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")

        logger.info(f"Fetched {len(amiibos)} amiibo entries")
        return {"count": len(amiibos), "output": str(output_path)}

    @staticmethod
    def _batch_export(kwargs: dict) -> dict:
        """Export amiibo data."""
        import json
        from amiibo_flipper.models import amiibo_from_api

        input_path = Path(kwargs.get("input", "data/amiibo.json"))
        output_path = Path(kwargs.get("output", "flipper-export/apps_data/amiibo_db"))
        file_format = kwargs.get("format", "txt")
        series = kwargs.get("series")
        character = kwargs.get("character")

        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        raw_payload = json.loads(input_path.read_text(encoding="utf-8"))
        raw_amiibos = raw_payload.get("amiibo", [])

        amiibos = [amiibo_from_api(item) for item in raw_amiibos if isinstance(item, dict)]

        # Apply filters
        if series:
            key = series.lower()
            amiibos = [a for a in amiibos if key in a.amiibo_series.lower()]
        if character:
            key = character.lower()
            amiibos = [a for a in amiibos if key in a.character.lower()]

        count = export_entries(amiibos, output_path, file_format=file_format)
        logger.info(f"Exported {count} entries")
        return {"count": count, "output": str(output_path)}

    @staticmethod
    def _batch_sync(kwargs: dict) -> dict:
        """Sync directly to Flipper SD."""
        sd_path_arg = kwargs.get("sd_path")
        if not sd_path_arg:
            raise ValueError("sd_path is required for sync command")
        sd_path = Path(sd_path_arg)
        file_format = kwargs.get("format", "txt")
        nfc_source = kwargs.get("nfc_source")
        series = kwargs.get("series")
        character = kwargs.get("character")

        if not sd_path.exists():
            raise FileNotFoundError(f"SD path not found: {sd_path}")

        amiibos = fetch_amiibos()

        # Apply filters
        if series:
            key = series.lower()
            amiibos = [a for a in amiibos if key in a.amiibo_series.lower()]
        if character:
            key = character.lower()
            amiibos = [a for a in amiibos if key in a.character.lower()]

        export_dir = sd_path / "apps_data" / "amiibo_db"
        count = export_entries(amiibos, export_dir, file_format=file_format)

        result = {"metadata_count": count}

        if nfc_source:
            nfc_target = sd_path / "nfc" / "amiibo"
            nfc_count = import_nfc_files(Path(nfc_source), nfc_target, overwrite=kwargs.get("overwrite_nfc", False))
            result["nfc_count"] = nfc_count

        logger.info(f"Synced {count} metadata entries")
        return result

    @staticmethod
    def _batch_convert_bin(kwargs: dict) -> dict:
        """Convert .bin to .nfc files."""
        source_arg = kwargs.get("source")
        output_arg = kwargs.get("output")
        if not source_arg:
            raise ValueError("source is required for convert-bin command")
        if not output_arg:
            raise ValueError("output is required for convert-bin command")

        source = Path(source_arg)
        output = Path(output_arg)
        overwrite = kwargs.get("overwrite", False)
        flatten = kwargs.get("flatten", False)

        if not source.exists():
            raise FileNotFoundError(f"Source directory not found: {source}")

        summary = convert_directory(source, output, overwrite=overwrite, flatten=flatten)
        logger.info(f"Converted {summary.converted} files")
        return {
            "converted": summary.converted,
            "skipped": summary.skipped_total,
            "output": str(output),
        }

    @staticmethod
    def _batch_download_images(kwargs: dict) -> dict:
        """Download amiibo images."""
        output = Path(kwargs.get("output", "data/images"))
        series = kwargs.get("series")
        character = kwargs.get("character")
        overwrite = kwargs.get("overwrite", False)

        amiibos = fetch_amiibos()

        # Apply filters
        if series:
            key = series.lower()
            amiibos = [a for a in amiibos if key in a.amiibo_series.lower()]
        if character:
            key = character.lower()
            amiibos = [a for a in amiibos if key in a.character.lower()]

        downloaded, skipped = download_images(amiibos, output, overwrite=overwrite)
        logger.info(f"Downloaded {downloaded} images")
        return {"downloaded": downloaded, "skipped": skipped, "output": str(output)}

    @staticmethod
    def _batch_inventory(kwargs: dict) -> dict:
        """Generate inventory report."""
        from amiibo_flipper.client import fetch_amiibos

        nfc_sources = kwargs.get("nfc_sources", [])
        output_path = kwargs.get("output")
        series = kwargs.get("series")
        character = kwargs.get("character")

        amiibos = fetch_amiibos()

        # Apply filters
        if series:
            key = series.lower()
            amiibos = [a for a in amiibos if key in a.amiibo_series.lower()]
        if character:
            key = character.lower()
            amiibos = [a for a in amiibos if key in a.character.lower()]

        nfc_paths = [Path(p) for p in nfc_sources]
        report = build_inventory(amiibos, nfc_paths)
        text = render_inventory_report(report)

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(text, encoding="utf-8")
            logger.info(f"Inventory report written to {output_path}")
            return {"output": str(output_path)}

        return {"report": text}


def create_batch_from_yaml(yaml_content: str) -> list[BatchCommand]:
    """Parse batch commands from YAML string.

    Example YAML:
        commands:
          - name: fetch
            output: data/amiibo.json
          - name: export
            input: data/amiibo.json
            output: flipper-export/apps_data/amiibo_db
          - name: download-images
            output: data/images
    """
    import yaml  # type: ignore
    config = yaml.safe_load(yaml_content)
    commands_data = config.get("commands", [])
    commands = [
        BatchCommand(
            name=cmd.get("name"),
            kwargs={k: v for k, v in cmd.items() if k != "name"},
        )
        for cmd in commands_data
    ]
    return commands
