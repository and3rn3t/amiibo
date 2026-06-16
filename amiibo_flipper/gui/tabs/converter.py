"""File conversion tab."""

import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QLabel,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from amiibo_flipper.gui.settings import GuiSettings, load_settings, save_settings
from amiibo_flipper.gui.widgets import Card, LogViewer, PathSelector, section_title
from amiibo_flipper.parallel import ConversionJob, convert_files_parallel

logger = logging.getLogger(__name__)


class ConversionWorker(QThread):
    """Worker thread for file conversions."""

    progress = pyqtSignal(int)
    log_message = pyqtSignal(str, str)  # message, level
    finished = pyqtSignal(bool, str)  # success, message

    def __init__(
        self,
        source: str,
        output: str,
        mode: str = "convert",
        workers: int = 4,
        overwrite: bool = False,
        flatten: bool = False,
    ):
        """Initialize worker thread.
        
        Args:
            source: Source directory path
            output: Output directory path
            mode: Operation mode ('convert', 'import-archive', 'check-duplicates')
            workers: Number of parallel workers
            overwrite: Whether to overwrite existing files
            flatten: Whether to flatten directory structure
        """
        super().__init__()
        self.source = source
        self.output = output
        self.mode = mode
        self.workers = workers
        self.overwrite = overwrite
        self.flatten = flatten

    def run(self) -> None:
        """Run the conversion operation."""
        try:
            if self.mode == "convert":
                self._convert_bin_files()
            elif self.mode == "import-archive":
                self._import_archive()
            else:
                self.finished.emit(False, f"Unknown mode: {self.mode}")
        except Exception as e:
            logger.exception("Conversion error")
            self.log_message.emit(str(e), "ERROR")
            self.finished.emit(False, str(e))

    def _convert_bin_files(self) -> None:
        """Convert .bin files to .nfc format."""
        try:
            source_path = Path(self.source)
            if not source_path.exists():
                raise ValueError(f"Source directory not found: {self.source}")

            # Find all .bin files
            bin_files = sorted(
                path
                for path in source_path.rglob("*")
                if path.is_file() and path.suffix.lower() == ".bin"
            )

            if not bin_files:
                self.log_message.emit("No .bin files found", "WARNING")
                self.finished.emit(True, "No files to convert")
                return

            self.log_message.emit(f"Found {len(bin_files)} .bin files", "INFO")

            # Create conversion jobs
            jobs = [
                ConversionJob(
                    source=str(f),
                    output=str(Path(self.output) / f"{f.stem}.nfc"),
                    overwrite=self.overwrite,
                )
                for f in bin_files
            ]

            # Run parallel conversion
            result = convert_files_parallel(jobs, self.workers)

            self.log_message.emit(
                f"Converted: {result.succeeded}, Skipped: {result.skipped}, Errors: {len(result.errors)}",
                "SUCCESS" if result.succeeded > 0 else "WARNING",
            )

            for error in result.errors:
                self.log_message.emit(f"Error: {error}", "ERROR")

            self.progress.emit(100)
            self.finished.emit(True, f"Completed: {result.succeeded} files converted")

        except Exception as e:
            logger.exception("Conversion error")
            raise

    def _import_archive(self) -> None:
        """Import files from archive."""
        from amiibo_flipper.archive import import_archive

        try:
            result = import_archive(
                self.source,
                self.output,
                flatten=self.flatten,
            )
            self.log_message.emit(f"Converted: {result.converted}", "INFO")
            self.log_message.emit(f"Skipped: {result.skipped}", "INFO")
            if result.errors:
                for error in result.errors:
                    self.log_message.emit(f"Error: {error}", "ERROR")
            self.progress.emit(100)
            self.finished.emit(True, "Archive import completed")
        except Exception as e:
            logger.exception("Archive import error")
            raise


class ConverterTab(QWidget):
    """Tab for file conversions."""

    def __init__(self):
        """Initialize converter tab."""
        super().__init__()
        self._settings = load_settings()
        self.worker: Optional[ConversionWorker] = None
        self._init_ui()
        self._load_defaults()

    def _init_ui(self) -> None:
        """Initialize UI."""
        layout = QVBoxLayout()
        layout.setSpacing(10)

        controls_card = Card()
        controls_card.layout.addWidget(section_title("Conversion"))

        mode_label = QLabel("Operation Mode")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Convert .bin files", "Import archive"])
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)
        controls_card.layout.addWidget(mode_label)
        controls_card.layout.addWidget(self.mode_combo)

        self.source_selector = PathSelector(
            "Source Directory:",
            is_directory=True,
        )
        controls_card.layout.addWidget(self.source_selector)

        self.output_selector = PathSelector(
            "Output Directory:",
            is_directory=True,
        )
        controls_card.layout.addWidget(self.output_selector)

        self.overwrite_check = QCheckBox("Overwrite existing files")
        self.flatten_check = QCheckBox("Flatten directory structure (archive mode)")
        self.flatten_check.setEnabled(False)
        controls_card.layout.addWidget(self.overwrite_check)
        controls_card.layout.addWidget(self.flatten_check)

        workers_label = QLabel("Parallel Workers")
        self.workers_spin = QSpinBox()
        self.workers_spin.setMinimum(1)
        self.workers_spin.setMaximum(16)
        self.workers_spin.setValue(4)
        controls_card.layout.addWidget(workers_label)
        controls_card.layout.addWidget(self.workers_spin)

        self.convert_btn = QPushButton("Start Conversion")
        self.convert_btn.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
        )
        self.convert_btn.clicked.connect(self._on_start_conversion)
        controls_card.layout.addWidget(self.convert_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        controls_card.layout.addWidget(self.progress_bar)

        layout.addWidget(controls_card)

        log_card = Card()
        log_card.layout.addWidget(section_title("Activity"))

        self.log_viewer = LogViewer()
        log_card.layout.addWidget(self.log_viewer, 1)

        self.clear_logs_btn = QPushButton("Clear Logs")
        self.clear_logs_btn.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogResetButton)
        )
        self.clear_logs_btn.clicked.connect(self.log_viewer.clear_logs)
        log_card.layout.addWidget(self.clear_logs_btn)

        layout.addWidget(log_card, 1)

        self.setLayout(layout)

    def _on_mode_changed(self, mode: str) -> None:
        """Handle mode change."""
        is_archive = "archive" in mode.lower()
        self.flatten_check.setEnabled(is_archive)

    def _on_start_conversion(self) -> None:
        """Start conversion."""
        source = self.source_selector.get_path()
        output = self.output_selector.get_path()

        if not source:
            self.log_viewer.append_log("Please select source directory", "ERROR")
            return

        if not output:
            self.log_viewer.append_log("Please select output directory", "ERROR")
            return

        # Determine mode
        mode = "import-archive" if "archive" in self.mode_combo.currentText().lower() else "convert"

        self._settings.converter_source_dir = source
        self._settings.converter_output_dir = output
        self._settings.converter_workers = self.workers_spin.value()
        self._settings.converter_overwrite = self.overwrite_check.isChecked()
        self._settings.converter_flatten = self.flatten_check.isChecked()
        save_settings(self._settings)

        self.convert_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.log_viewer.append_log(f"Starting {mode}...", "INFO")

        self.worker = ConversionWorker(
            source=source,
            output=output,
            mode=mode,
            workers=self.workers_spin.value(),
            overwrite=self.overwrite_check.isChecked(),
            flatten=self.flatten_check.isChecked(),
        )

        self.worker.log_message.connect(self.log_viewer.append_log)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.finished.connect(self._on_conversion_finished)
        self.worker.start()

    def _on_conversion_finished(self, success: bool, message: str) -> None:
        """Handle conversion completion."""
        level = "SUCCESS" if success else "ERROR"
        self.log_viewer.append_log(message, level)
        self.convert_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

    def _load_defaults(self) -> None:
        """Apply saved defaults to form controls."""
        if self._settings.converter_source_dir:
            self.source_selector.set_path(self._settings.converter_source_dir)
        if self._settings.converter_output_dir:
            self.output_selector.set_path(self._settings.converter_output_dir)
        self.workers_spin.setValue(self._settings.converter_workers)
        self.overwrite_check.setChecked(self._settings.converter_overwrite)
        self.flatten_check.setChecked(self._settings.converter_flatten)

    def apply_settings(self, settings: GuiSettings) -> None:
        """Apply settings pushed from the Settings tab."""
        self._settings = settings
        self._load_defaults()
