"""Tests for config module."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from amiibo_flipper.config import AmiiboConfig, load_config, save_config_template


def test_default_config() -> None:
    """Test that default config has expected values."""
    config = AmiiboConfig()
    assert config.amiibo_json == Path("data/amiibo.json")
    assert config.export_dir == Path("flipper-export/apps_data/amiibo_db")
    assert config.sd_nfc_dir == Path("nfc/amiibo")
    assert config.desktop_name == "flipper-amiibo"
    assert config.default_series is None
    assert config.default_character is None


def test_load_config_missing_file() -> None:
    """Test that missing config file returns defaults."""
    with tempfile.TemporaryDirectory() as tmpdir:
        old_cwd = Path.cwd()
        try:
            import os
            os.chdir(tmpdir)
            config = load_config()
            assert config.amiibo_json == Path("data/amiibo.json")
        finally:
            os.chdir(old_cwd)


def test_load_config_yaml() -> None:
    """Test loading from YAML config."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / ".amiibo.yml"
        config_path.write_text("""
amiibo_json: custom/amiibo.json
export_dir: custom/export
default_series: Mario
""")
        config = load_config(config_path)
        assert config.amiibo_json == Path("custom/amiibo.json")
        assert config.export_dir == Path("custom/export")
        assert config.default_series == "Mario"


def test_load_config_json() -> None:
    """Test loading from JSON config."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / ".amiibo.json"
        config_path.write_text(json.dumps({
            "amiibo_json": "data/amiibo.json",
            "desktop_name": "my-amiibo",
        }))
        config = load_config(config_path)
        assert config.desktop_name == "my-amiibo"


def test_save_config_template() -> None:
    """Test that template is created with expected structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        template_path = Path(tmpdir) / ".amiibo.yml"
        save_config_template(template_path)
        assert template_path.exists()
        content = template_path.read_text()
        assert "amiibo_json" in content
        assert "export_dir" in content
        assert "default_series" in content
