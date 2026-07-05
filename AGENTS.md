# AGENTS.md — amiibo-flipper

Python CLI (+ optional GUI) that fetches amiibo metadata and exports Flipper Zero-friendly files for browsing on an SD card.

## Stack

- Python `>=3.10`, pyproject.toml (setuptools); package `amiibo_flipper/`
- Entry points: `amiibo-flipper` (CLI, `cli.py`) and `amiibo-flipper-gui` (`gui/main_window.py`)
- Tests: pytest in `tests/`
- PyInstaller builds (`build-macos.sh`, `amiibo_flipper_gui.spec`)

## Commands

```bash
pip install -e ".[dev]"    # in a venv (or --break-system-packages)
pytest                     # run tests
amiibo-flipper --help      # CLI
```

## Conventions

- Key modules: `client.py` (API fetch), `converter.py`/`exporter.py` (Flipper file formats), `batch.py`, `duplicates.py`, `archive.py`, `config.py` (see `CONFIG.md`).
- `ADVANCED.md` and `GUI.md` document extended usage; keep them in sync with behavior changes.
- Exported file formats must remain Flipper-compatible — don't change output structure without checking Flipper NFC file specs.
- Conventional commits: `type(scope): description`.
- Don't commit or publish builds unless explicitly asked.
