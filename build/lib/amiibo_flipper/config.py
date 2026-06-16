"""Configuration file support for amiibo-flipper."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

import yaml  # type: ignore


logger = logging.getLogger(__name__)


@dataclass
class AmiiboConfig:
    """Configuration settings loaded from .amiibo.yml or .amiibo.json."""

    amiibo_json: Path = Path("data/amiibo.json")
    export_dir: Path = Path("flipper-export/apps_data/amiibo_db")
    sd_nfc_dir: Path = Path("nfc/amiibo")
    desktop_name: str = "flipper-amiibo"
    default_series: str | None = None
    default_character: str | None = None
    extra_options: dict = field(default_factory=dict)


def load_config(config_path: Path | None = None) -> AmiiboConfig:
    """Load config from file, or return defaults if no file found.

    Searches in this order:
    1. Specified config_path
    2. .amiibo.yml in current directory
    3. .amiibo.json in current directory
    4. Returns defaults
    """
    candidates = []
    if config_path:
        candidates.append(config_path)
    candidates.extend([
        Path(".amiibo.yml"),
        Path(".amiibo.json"),
    ])

    for path in candidates:
        if path.exists():
            try:
                return _parse_config(path)
            except Exception as e:
                logger.warning(f"Failed to load config from {path}: {e}")

    logger.debug("No config file found; using defaults")
    return AmiiboConfig()


def _parse_config(path: Path) -> AmiiboConfig:
    """Parse YAML or JSON config file."""
    text = path.read_text()

    if path.suffix == ".yml" or path.suffix == ".yaml":
        data = yaml.safe_load(text) or {}
    else:
        data = json.loads(text)

    logger.debug(f"Loaded config from {path}")

    # Map config keys to dataclass fields
    amiibo_json = data.get("amiibo_json")
    export_dir = data.get("export_dir")
    sd_nfc_dir = data.get("sd_nfc_dir")
    desktop_name = data.get("desktop_name")
    default_series = data.get("default_series")
    default_character = data.get("default_character")

    return AmiiboConfig(
        amiibo_json=Path(amiibo_json) if amiibo_json else Path("data/amiibo.json"),
        export_dir=Path(export_dir) if export_dir else Path("flipper-export/apps_data/amiibo_db"),
        sd_nfc_dir=Path(sd_nfc_dir) if sd_nfc_dir else Path("nfc/amiibo"),
        desktop_name=desktop_name or "flipper-amiibo",
        default_series=default_series,
        default_character=default_character,
        extra_options=data.get("extra_options", {}),
    )


def save_config_template(path: Path = Path(".amiibo.yml")) -> None:
    """Write a template config file."""
    template = """# amiibo-flipper configuration

# Paths to key data files
amiibo_json: data/amiibo.json
export_dir: flipper-export/apps_data/amiibo_db
sd_nfc_dir: nfc/amiibo

# Desktop staging folder name (when using --desktop flag)
desktop_name: flipper-amiibo

# Default filters (can be overridden per command)
default_series: ~  # e.g., "Zelda", "Mario", "Animal Crossing"
default_character: ~  # e.g., "Link", "Mario", "Isabelle"

# Extra options (reserved for future use)
extra_options: {}
"""
    path.write_text(template)
    logger.info(f"Wrote config template to {path}")
