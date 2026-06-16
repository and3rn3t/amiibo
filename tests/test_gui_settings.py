"""Tests for GUI settings persistence."""

from pathlib import Path

from amiibo_flipper.gui.settings import GuiSettings, load_settings, save_settings


def test_load_settings_defaults_when_missing(tmp_path: Path) -> None:
    settings_path = tmp_path / "gui.json"
    settings = load_settings(settings_path)

    assert settings.converter_workers == 4
    assert settings.converter_source_dir == ""
    assert settings.batch_file == ""


def test_save_and_load_settings_roundtrip(tmp_path: Path) -> None:
    settings_path = tmp_path / "gui.json"
    original = GuiSettings(
        converter_source_dir="/tmp/source",
        converter_output_dir="/tmp/output",
        converter_workers=8,
        converter_overwrite=True,
        converter_flatten=True,
        watch_source_dir="/tmp/watch-source",
        watch_output_dir="/tmp/watch-output",
        watch_overwrite=True,
        watch_flatten=False,
        batch_file="/tmp/workflow.yml",
    )

    save_settings(original, settings_path)
    loaded = load_settings(settings_path)

    assert loaded == original


def test_load_settings_ignores_invalid_content(tmp_path: Path) -> None:
    settings_path = tmp_path / "gui.json"
    settings_path.write_text("not-json", encoding="utf-8")

    loaded = load_settings(settings_path)

    assert loaded == GuiSettings()
