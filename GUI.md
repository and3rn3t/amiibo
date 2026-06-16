# amiibo-flipper GUI

A modern graphical interface for amiibo-flipper that brings file conversion, batch operations, and workflows to a user-friendly desktop application.

## Installation

The GUI is available as an optional feature. Install it with:

```bash
pip install amiibo-flipper[gui]
```

Or if you're developing:

```bash
pip install -e ".[gui]"
```

## Launching the GUI

```bash
amiibo-flipper-gui
```

Or from Python:

```python
from amiibo_flipper.gui.main_window import main
main()
```

## Features

### 1. Converter Tab

Convert `.bin` files to `.nfc` format or import archives with a visual interface.

**Operations:**
- **Convert .bin files** — Parallel conversion of multiple files
- **Import archive** — Extract and convert ZIP archives in one operation

**Options:**
- **Source Directory** — Directory containing `.bin` files or archive
- **Output Directory** — Where to save `.nfc` files
- **Overwrite existing files** — Replace if output already exists
- **Flatten directory structure** — Archive mode only; remove nested folders
- **Parallel Workers** — Number of concurrent conversion threads (1-16)

**Real-time Log Viewer:**
- Shows conversion progress and status
- Color-coded messages (INFO, ERROR, WARNING, SUCCESS)
- Clear logs button for cleanup

### 2. Batch Runner Tab

Execute complex workflows from YAML batch files without touching the CLI.

**Steps:**
1. Click "Browse..." and select a batch YAML file
2. Click "Run Batch" to execute all commands sequentially
3. Monitor progress in the live log viewer

**Supported Commands in Batch Files:**
- `fetch` — Download amiibo metadata
- `export` — Export to Flipper format
- `sync` — Sync to Flipper device
- `convert-bin` — Convert .bin files
- `download-images` — Fetch amiibo images
- `inventory` — Generate collection inventory

**Example Batch File (workflow.yml):**

```yaml
commands:
  - name: fetch
    output: data/amiibo.json
  
  - name: export
    input: data/amiibo.json
    output: flipper-export/apps_data/amiibo_db
  
  - name: convert-bin-parallel
    source: to-convert/
    output: nfc/amiibo
    workers: 8
  
  - name: sync
    sd_path: /Volumes/FLIP
    nfc_source: nfc/amiibo
```

## Architecture

```
amiibo_flipper/gui/
├── main_window.py      # Application entry point
├── widgets.py          # Reusable components (PathSelector, LogViewer)
└── tabs/
    ├── converter.py    # File conversion interface
    └── batch_runner.py # Batch workflow execution
```

## Threading Model

Both tabs use QThread to run long-running operations without freezing the UI:

- **ConversionWorker** — Handles file conversions in background
- **BatchWorker** — Executes batch commands sequentially
- **LogViewer** — Receives updates via PyQt signals

## Code Reuse

The GUI shares all conversion and batch logic with the CLI:

- `amiibo_flipper.converter.bin_to_nfc()` — File conversion
- `amiibo_flipper.parallel.convert_files_parallel()` — Parallel processing
- `amiibo_flipper.batch.BatchRunner` — Batch execution
- `amiibo_flipper.archive.import_archive()` — Archive import

This means bug fixes and features automatically benefit both interfaces.

## Development

### Adding a New Tab

1. Create a new file in `amiibo_flipper/gui/tabs/`
2. Subclass `QWidget` and implement `_init_ui()`
3. Import in `amiibo_flipper/gui/tabs/__init__.py`
4. Add to tab widget in `amiibo_flipper/gui/main_window.py`

Example:

```python
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton

class MyTab(QWidget):
    def __init__(self):
        super().__init__()
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout()
        btn = QPushButton("Click me!")
        layout.addWidget(btn)
        self.setLayout(layout)
```

### Running Tests

```bash
pytest tests/test_gui.py -v
```

## Troubleshooting

### "No module named PyQt6"

Install the GUI extra:

```bash
pip install amiibo-flipper[gui]
```

### GUI doesn't start

Check Python version (3.10+ required):

```bash
python --version
```

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
from amiibo_flipper.gui.main_window import main
main()
```

### Conversion slow

Increase workers in the Converter tab (up to CPU count recommended). Default is 4.

## Future Enhancements

- Watch mode tab with real-time monitoring
- Duplicates scanner with visual duplicate grouping
- Statistics dashboard showing collection metrics
- Drag-and-drop file support
- System tray icon with quick actions
- Batch job scheduling
- Progress visualization graphs

## Performance

The GUI uses the same optimized conversion engine as the CLI:

- **Parallel conversions** — 5-8x faster than sequential
- **Efficient archive import** — Stream extraction without temp bloat
- **Non-blocking UI** — All operations run in background threads

Typical performance:
- 100 files: 2-5 seconds (8 workers)
- 1000 files: 20-40 seconds (8 workers)
