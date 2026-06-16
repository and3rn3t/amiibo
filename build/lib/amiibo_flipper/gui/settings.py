"""Persistent settings for the amiibo-flipper GUI."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


SETTINGS_PATH = Path.home() / ".amiibo-flipper-gui.json"


@dataclass
class GuiSettings:
    """Serializable user settings for GUI defaults."""

    converter_source_dir: str = ""
    converter_output_dir: str = ""
    converter_workers: int = 4
    converter_overwrite: bool = False
    converter_flatten: bool = False
    watch_source_dir: str = ""
    watch_output_dir: str = ""
    watch_overwrite: bool = False
    watch_flatten: bool = False
    batch_file: str = ""
    theme: str = "light"
    compact_mode: bool = False


def load_settings(path: Path = SETTINGS_PATH) -> GuiSettings:
    """Load settings from disk, falling back to defaults when missing/invalid."""
    if not path.exists():
        return GuiSettings()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return GuiSettings()

        defaults = asdict(GuiSettings())
        defaults.update({k: v for k, v in data.items() if k in defaults})
        return GuiSettings(**defaults)
    except Exception:
        return GuiSettings()


def save_settings(settings: GuiSettings, path: Path = SETTINGS_PATH) -> None:
    """Save settings to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")
