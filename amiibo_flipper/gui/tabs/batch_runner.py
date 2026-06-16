"""Batch operations tab."""

import logging
from typing import Optional

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QLabel,
    QPushButton,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from amiibo_flipper.batch import BatchRunner, create_batch_from_yaml
from amiibo_flipper.gui.settings import GuiSettings, load_settings, save_settings
from amiibo_flipper.gui.widgets import Card, LogViewer, PathSelector, section_title

logger = logging.getLogger(__name__)


class BatchWorker(QThread):
    """Worker thread for batch operations."""

    log_message = pyqtSignal(str, str)  # message, level
    finished = pyqtSignal(bool, str)  # success, message

    def __init__(self, batch_file: str):
        """Initialize worker thread.
        
        Args:
            batch_file: Path to batch YAML file
        """
        super().__init__()
        self.batch_file = batch_file

    def run(self) -> None:
        """Run the batch operations."""
        try:
            batch = create_batch_from_yaml(self.batch_file)
            runner = BatchRunner()

            for command in batch.commands:
                self.log_message.emit(f"Running: {command.name}", "INFO")

            result = runner.run(batch)

            if result.succeeded == len(batch.commands):
                msg = f"All {result.succeeded} commands completed successfully"
                self.log_message.emit(msg, "SUCCESS")
                self.finished.emit(True, msg)
            else:
                msg = f"Completed with {len(result.errors)} error(s)"
                self.log_message.emit(msg, "WARNING")
                for error in result.errors:
                    self.log_message.emit(f"  - {error}", "ERROR")
                self.finished.emit(result.succeeded > 0, msg)

        except Exception as e:
            logger.exception("Batch execution error")
            self.log_message.emit(str(e), "ERROR")
            self.finished.emit(False, str(e))


class BatchRunnerTab(QWidget):
    """Tab for batch operations."""

    def __init__(self):
        """Initialize batch runner tab."""
        super().__init__()
        self._settings = load_settings()
        self.worker: Optional[BatchWorker] = None
        self._init_ui()
        self._load_defaults()

    def _init_ui(self) -> None:
        """Initialize UI."""
        layout = QVBoxLayout()
        layout.setSpacing(10)

        controls_card = Card()
        controls_card.layout.addWidget(section_title("Batch Runner"))

        # File selection
        self.file_selector = PathSelector(
            "Batch File (.yml):",
            is_directory=False,
        )
        controls_card.layout.addWidget(self.file_selector)

        # Info text
        info_label = QLabel(
            "Select a YAML batch file containing commands to execute.\n"
            "Format: commands with name, input, output, and other options."
        )
        info_label.setWordWrap(True)
        controls_card.layout.addWidget(info_label)

        # Run button
        self.run_btn = QPushButton("Run Batch")
        self.run_btn.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
        )
        self.run_btn.clicked.connect(self._on_run_batch)
        controls_card.layout.addWidget(self.run_btn)

        layout.addWidget(controls_card)

        log_card = Card()
        log_card.layout.addWidget(section_title("Execution Log"))

        self.log_viewer = LogViewer()
        log_card.layout.addWidget(self.log_viewer, 1)

        # Clear logs button
        self.clear_logs_btn = QPushButton("Clear Logs")
        self.clear_logs_btn.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogResetButton)
        )
        self.clear_logs_btn.clicked.connect(self.log_viewer.clear_logs)
        log_card.layout.addWidget(self.clear_logs_btn)

        layout.addWidget(log_card, 1)

        self.setLayout(layout)

    def _on_run_batch(self) -> None:
        """Run batch operations."""
        batch_file = self.file_selector.get_path()

        if not batch_file:
            self.log_viewer.append_log("Please select a batch file", "ERROR")
            return

        self._settings.batch_file = batch_file
        save_settings(self._settings)

        self.run_btn.setEnabled(False)
        self.log_viewer.append_log(f"Loading batch file: {batch_file}", "INFO")

        self.worker = BatchWorker(batch_file)
        self.worker.log_message.connect(self.log_viewer.append_log)
        self.worker.finished.connect(self._on_batch_finished)
        self.worker.start()

    def _on_batch_finished(self, success: bool, message: str) -> None:
        """Handle batch completion."""
        level = "SUCCESS" if success else "ERROR"
        self.log_viewer.append_log(message, level)
        self.run_btn.setEnabled(True)

    def _load_defaults(self) -> None:
        """Apply saved defaults to form controls."""
        if self._settings.batch_file:
            self.file_selector.set_path(self._settings.batch_file)

    def apply_settings(self, settings: GuiSettings) -> None:
        """Apply settings pushed from the Settings tab."""
        self._settings = settings
        self._load_defaults()
