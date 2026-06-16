"""Duplicate scanning tab."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QLabel,
    QPushButton,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from amiibo_flipper.duplicates import (
    DuplicateScanResult,
    format_duplicates_for_display,
    save_duplication_report,
    scan_for_duplicates,
)
from amiibo_flipper.gui.widgets import Card, LogViewer, PathSelector, section_title

logger = logging.getLogger(__name__)


class DuplicateWorker(QThread):
    """Background worker for duplicate scanning."""

    log_message = pyqtSignal(str, str)
    finished = pyqtSignal(object)  # DuplicateScanResult
    failed = pyqtSignal(str)

    def __init__(self, source: str, report_path: Optional[str] = None):
        super().__init__()
        self.source = source
        self.report_path = report_path

    def run(self) -> None:
        try:
            source_path = Path(self.source)
            if not source_path.exists():
                raise ValueError(f"Source directory not found: {source_path}")

            self.log_message.emit("Scanning for duplicates...", "INFO")
            result = scan_for_duplicates(source_path)

            if self.report_path:
                output = Path(self.report_path)
                output.parent.mkdir(parents=True, exist_ok=True)
                save_duplication_report(result, output)
                self.log_message.emit(f"Saved JSON report to {output}", "INFO")

            self.finished.emit(result)
        except Exception as exc:  # pragma: no cover - Qt thread boundary
            logger.exception("Duplicate scan failed")
            self.failed.emit(str(exc))


class DuplicatesTab(QWidget):
    """Tab for duplicate detection and reporting."""

    def __init__(self):
        super().__init__()
        self.worker: Optional[DuplicateWorker] = None
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout()
        layout.setSpacing(10)

        controls_card = Card()
        controls_card.layout.addWidget(section_title("Duplicate Scanner"))

        self.source_selector = PathSelector("Scan Directory:", is_directory=True)
        controls_card.layout.addWidget(self.source_selector)

        self.save_report_check = QCheckBox("Save JSON report")
        self.save_report_check.toggled.connect(self._on_report_toggle)
        controls_card.layout.addWidget(self.save_report_check)

        self.report_selector = PathSelector("Report File:", is_directory=False)
        self.report_selector.setEnabled(False)
        controls_card.layout.addWidget(self.report_selector)

        self.scan_btn = QPushButton("Scan Duplicates")
        self.scan_btn.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView)
        )
        self.scan_btn.clicked.connect(self._on_scan)
        controls_card.layout.addWidget(self.scan_btn)

        self.summary_label = QLabel("No scan run yet")
        controls_card.layout.addWidget(self.summary_label)

        layout.addWidget(controls_card)

        results_card = Card()
        results_card.layout.addWidget(section_title("Results"))
        self.log_viewer = LogViewer()
        results_card.layout.addWidget(self.log_viewer, 1)

        self.clear_logs_btn = QPushButton("Clear Logs")
        self.clear_logs_btn.setProperty("variant", "secondary")
        self.clear_logs_btn.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogResetButton)
        )
        self.clear_logs_btn.clicked.connect(self.log_viewer.clear_logs)
        results_card.layout.addWidget(self.clear_logs_btn)

        layout.addWidget(results_card, 1)

        self.setLayout(layout)

    def _on_report_toggle(self, checked: bool) -> None:
        self.report_selector.setEnabled(checked)

    def _on_scan(self) -> None:
        source = self.source_selector.get_path().strip()
        if not source:
            self.log_viewer.append_log("Please select a scan directory", "ERROR")
            return

        report_path: Optional[str] = None
        if self.save_report_check.isChecked():
            report_path = self.report_selector.get_path().strip()
            if not report_path:
                self.log_viewer.append_log("Please select a report file path", "ERROR")
                return

        self.scan_btn.setEnabled(False)
        self.summary_label.setText("Scanning...")

        self.worker = DuplicateWorker(source=source, report_path=report_path)
        self.worker.log_message.connect(self.log_viewer.append_log)
        self.worker.finished.connect(self._on_finished)
        self.worker.failed.connect(self._on_failed)
        self.worker.start()

    def _on_finished(self, result: DuplicateScanResult) -> None:
        self.scan_btn.setEnabled(True)
        self.summary_label.setText(
            f"Scanned {result.total_files} files, found {result.duplicates_found} duplicates"
        )

        display = format_duplicates_for_display(result)
        level = "WARNING" if result.duplicates_found else "SUCCESS"
        for line in display.splitlines():
            if line.strip():
                self.log_viewer.append_log(line, level)

    def _on_failed(self, message: str) -> None:
        self.scan_btn.setEnabled(True)
        self.summary_label.setText("Scan failed")
        self.log_viewer.append_log(message, "ERROR")
