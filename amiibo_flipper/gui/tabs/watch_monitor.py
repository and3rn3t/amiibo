"""Watch mode tab for live auto-conversion monitoring."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QLabel,
    QPushButton,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from amiibo_flipper.converter import bin_to_nfc
from amiibo_flipper.gui.settings import GuiSettings, load_settings, save_settings
from amiibo_flipper.gui.widgets import Card, LogViewer, PathSelector, section_title

logger = logging.getLogger(__name__)


class WatchWorker(QThread):
    """Background thread for directory watch mode."""

    log_message = pyqtSignal(str, str)
    stats_updated = pyqtSignal(int, int, int, float)
    running_changed = pyqtSignal(bool)

    def __init__(
        self,
        source_dir: str,
        output_dir: str,
        flatten: bool,
        overwrite: bool,
    ):
        super().__init__()
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.flatten = flatten
        self.overwrite = overwrite
        self._should_stop = False

    def stop(self) -> None:
        """Signal the watch loop to stop."""
        self._should_stop = True

    def run(self) -> None:
        """Start and run the watch observer until stop is requested."""
        observer = None
        start_time = time.time()

        try:
            from watchdog.observers import Observer
            from amiibo_flipper.watch import _ConversionHandler
        except ImportError:
            self.log_message.emit(
                "watchdog package required for watch mode. Install with: pip install watchdog",
                "ERROR",
            )
            self.running_changed.emit(False)
            return

        if not self.source_dir.exists():
            self.log_message.emit(f"Source directory not found: {self.source_dir}", "ERROR")
            self.running_changed.emit(False)
            return

        self.output_dir.mkdir(parents=True, exist_ok=True)

        def convert_single_file(source: Path, output_dir: Path, flatten: bool, overwrite: bool) -> dict[str, object]:
            try:
                if source.suffix.lower() != ".bin":
                    reason = "Only .bin files are converted"
                    self.log_message.emit(f"Skipped {source.name}: {reason}", "WARNING")
                    return {"success": False, "reason": reason}

                data = source.read_bytes()
                if len(data) != 540:
                    reason = f"Invalid size: {len(data)}"
                    self.log_message.emit(f"Skipped {source.name}: {reason}", "WARNING")
                    return {"success": False, "reason": reason}

                nfc_content = bin_to_nfc(data)

                if flatten:
                    output_file = output_dir / f"{source.stem}.nfc"
                else:
                    rel_path = source.relative_to(self.source_dir)
                    output_file = output_dir / rel_path.with_suffix(".nfc")

                if output_file.exists() and not overwrite:
                    reason = "File exists"
                    self.log_message.emit(f"Skipped {source.name}: {reason}", "WARNING")
                    return {"success": False, "reason": reason}

                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text(nfc_content, encoding="utf-8")
                self.log_message.emit(f"Converted {source.name} -> {output_file.name}", "SUCCESS")
                return {"success": True}
            except Exception as exc:
                reason = str(exc)
                self.log_message.emit(f"Error converting {source.name}: {reason}", "ERROR")
                return {"success": False, "reason": reason}

        handler = _ConversionHandler(
            source_dir=self.source_dir,
            output_dir=self.output_dir,
            convert_func=convert_single_file,
            flatten=self.flatten,
            overwrite=self.overwrite,
        )

        observer = Observer()
        observer.schedule(handler, str(self.source_dir), recursive=True)
        observer.start()
        self.running_changed.emit(True)
        self.log_message.emit(f"Watching {self.source_dir}", "SUCCESS")

        try:
            while not self._should_stop:
                duration = time.time() - start_time
                self.stats_updated.emit(
                    handler.stats.files_converted,
                    handler.stats.files_skipped,
                    handler.stats.errors,
                    duration,
                )
                time.sleep(0.5)
        finally:
            if observer is not None:
                observer.stop()
                observer.join()

            duration = time.time() - start_time
            self.stats_updated.emit(
                handler.stats.files_converted,
                handler.stats.files_skipped,
                handler.stats.errors,
                duration,
            )
            self.log_message.emit("Watch session stopped", "INFO")
            self.running_changed.emit(False)


class WatchTab(QWidget):
    """Tab for live watch mode monitoring."""

    def __init__(self):
        super().__init__()
        self._settings = load_settings()
        self.worker: Optional[WatchWorker] = None
        self._init_ui()
        self._load_defaults()

    def _init_ui(self) -> None:
        layout = QVBoxLayout()
        layout.setSpacing(10)

        self.source_selector = PathSelector("Watch Directory:", is_directory=True)
        self.output_selector = PathSelector("Output Directory:", is_directory=True)
        controls_card = Card()
        controls_card.layout.addWidget(section_title("Watch Mode"))
        controls_card.layout.addWidget(self.source_selector)
        controls_card.layout.addWidget(self.output_selector)

        self.flatten_check = QCheckBox("Flatten output directory structure")
        self.overwrite_check = QCheckBox("Overwrite existing files")
        controls_card.layout.addWidget(self.flatten_check)
        controls_card.layout.addWidget(self.overwrite_check)

        self.start_btn = QPushButton("Start Watch")
        self.start_btn.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
        )
        self.start_btn.clicked.connect(self._on_start)
        self.stop_btn = QPushButton("Stop Watch")
        self.stop_btn.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop)
        )
        self.stop_btn.clicked.connect(self._on_stop)
        self.stop_btn.setEnabled(False)
        controls_card.layout.addWidget(self.start_btn)
        controls_card.layout.addWidget(self.stop_btn)

        layout.addWidget(controls_card)

        stats_card = Card()
        stats_card.layout.addWidget(section_title("Session Stats"))

        stats_grid = QGridLayout()
        self.converted_label = QLabel("Converted: 0")
        self.skipped_label = QLabel("Skipped: 0")
        self.errors_label = QLabel("Errors: 0")
        self.duration_label = QLabel("Duration: 0.0s")
        stats_grid.addWidget(self.converted_label, 0, 0)
        stats_grid.addWidget(self.skipped_label, 0, 1)
        stats_grid.addWidget(self.errors_label, 1, 0)
        stats_grid.addWidget(self.duration_label, 1, 1)
        stats_card.layout.addLayout(stats_grid)
        layout.addWidget(stats_card)

        log_card = Card()
        log_card.layout.addWidget(section_title("Live Events"))
        self.log_viewer = LogViewer()
        log_card.layout.addWidget(self.log_viewer, 1)
        layout.addWidget(log_card, 1)

        self.setLayout(layout)

    def _on_start(self) -> None:
        source = self.source_selector.get_path().strip()
        output = self.output_selector.get_path().strip()

        if not source:
            self.log_viewer.append_log("Please select a watch directory", "ERROR")
            return
        if not output:
            self.log_viewer.append_log("Please select an output directory", "ERROR")
            return

        self._settings.watch_source_dir = source
        self._settings.watch_output_dir = output
        self._settings.watch_flatten = self.flatten_check.isChecked()
        self._settings.watch_overwrite = self.overwrite_check.isChecked()
        save_settings(self._settings)

        self._set_running_ui(True)
        self.worker = WatchWorker(
            source_dir=source,
            output_dir=output,
            flatten=self.flatten_check.isChecked(),
            overwrite=self.overwrite_check.isChecked(),
        )
        self.worker.log_message.connect(self.log_viewer.append_log)
        self.worker.stats_updated.connect(self._on_stats_updated)
        self.worker.running_changed.connect(self._set_running_ui)
        self.worker.start()

    def _on_stop(self) -> None:
        if self.worker is not None:
            self.worker.stop()

    def _on_stats_updated(self, converted: int, skipped: int, errors: int, duration: float) -> None:
        self.converted_label.setText(f"Converted: {converted}")
        self.skipped_label.setText(f"Skipped: {skipped}")
        self.errors_label.setText(f"Errors: {errors}")
        self.duration_label.setText(f"Duration: {duration:.1f}s")

    def _set_running_ui(self, running: bool) -> None:
        self.start_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)

    def _load_defaults(self) -> None:
        """Apply saved defaults to form controls."""
        if self._settings.watch_source_dir:
            self.source_selector.set_path(self._settings.watch_source_dir)
        if self._settings.watch_output_dir:
            self.output_selector.set_path(self._settings.watch_output_dir)
        self.flatten_check.setChecked(self._settings.watch_flatten)
        self.overwrite_check.setChecked(self._settings.watch_overwrite)

    def apply_settings(self, settings: GuiSettings) -> None:
        """Apply settings pushed from the Settings tab."""
        self._settings = settings
        self._load_defaults()
