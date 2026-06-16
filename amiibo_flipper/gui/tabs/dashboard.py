"""Dashboard tab for quick collection stats."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QGridLayout,
    QLabel,
    QPushButton,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from amiibo_flipper.duplicates import scan_for_duplicates
from amiibo_flipper.gui.widgets import Card, LogViewer, PathSelector, section_title


@dataclass
class DashboardStats:
    """Computed dashboard metrics for a directory."""

    total_files: int
    nfc_files: int
    bin_files: int
    duplicate_files: int
    duplicate_groups: int
    total_bytes: int


def compute_dashboard_stats(directory: Path) -> DashboardStats:
    """Compute quick stats for NFC/BIN files in a directory tree."""
    nfc_files = 0
    bin_files = 0
    total_bytes = 0

    for file_path in directory.rglob("*"):
        if not file_path.is_file():
            continue
        suffix = file_path.suffix.lower()
        if suffix == ".nfc":
            nfc_files += 1
            total_bytes += file_path.stat().st_size
        elif suffix == ".bin":
            bin_files += 1
            total_bytes += file_path.stat().st_size

    dup_result = scan_for_duplicates(directory)

    return DashboardStats(
        total_files=nfc_files + bin_files,
        nfc_files=nfc_files,
        bin_files=bin_files,
        duplicate_files=dup_result.duplicates_found,
        duplicate_groups=len(dup_result.duplicate_groups),
        total_bytes=total_bytes,
    )


class DashboardTab(QWidget):
    """Dashboard for at-a-glance collection health and size."""

    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout()
        layout.setSpacing(10)

        controls_card = Card()
        controls_card.layout.addWidget(section_title("Collection Overview"))

        self.source_selector = PathSelector("Collection Directory:", is_directory=True)
        controls_card.layout.addWidget(self.source_selector)

        self.refresh_btn = QPushButton("Refresh Dashboard")
        self.refresh_btn.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload)
        )
        self.refresh_btn.clicked.connect(self._on_refresh)
        controls_card.layout.addWidget(self.refresh_btn)

        layout.addWidget(controls_card)

        stats_card = Card()
        stats_card.layout.addWidget(section_title("Metrics"))

        stats_grid = QGridLayout()
        self.total_label = QLabel("Total files: -")
        self.nfc_label = QLabel(".nfc files: -")
        self.bin_label = QLabel(".bin files: -")
        self.dup_label = QLabel("Duplicate files: -")
        self.group_label = QLabel("Duplicate groups: -")
        self.size_label = QLabel("Total size: -")
        self.updated_label = QLabel("Last updated: -")

        stats_grid.addWidget(self.total_label, 0, 0)
        stats_grid.addWidget(self.nfc_label, 0, 1)
        stats_grid.addWidget(self.bin_label, 1, 0)
        stats_grid.addWidget(self.dup_label, 1, 1)
        stats_grid.addWidget(self.group_label, 2, 0)
        stats_grid.addWidget(self.size_label, 2, 1)
        stats_grid.addWidget(self.updated_label, 3, 0, 1, 2)
        stats_card.layout.addLayout(stats_grid)
        layout.addWidget(stats_card)

        log_card = Card()
        log_card.layout.addWidget(section_title("Activity"))
        self.log_viewer = LogViewer()
        log_card.layout.addWidget(self.log_viewer, 1)

        layout.addWidget(log_card, 1)

        self.setLayout(layout)

    def _on_refresh(self) -> None:
        source = self.source_selector.get_path().strip()
        if not source:
            self.log_viewer.append_log("Please select a collection directory", "ERROR")
            return

        directory = Path(source)
        if not directory.exists():
            self.log_viewer.append_log(f"Directory not found: {directory}", "ERROR")
            return

        stats = compute_dashboard_stats(directory)
        self.total_label.setText(f"Total files: {stats.total_files}")
        self.nfc_label.setText(f".nfc files: {stats.nfc_files}")
        self.bin_label.setText(f".bin files: {stats.bin_files}")
        self.dup_label.setText(f"Duplicate files: {stats.duplicate_files}")
        self.group_label.setText(f"Duplicate groups: {stats.duplicate_groups}")
        self.size_label.setText(f"Total size: {self._format_bytes(stats.total_bytes)}")
        self.updated_label.setText(
            f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        self.log_viewer.append_log("Dashboard refreshed", "SUCCESS")

    @staticmethod
    def _format_bytes(total_bytes: int) -> str:
        units = ["B", "KB", "MB", "GB", "TB"]
        size = float(total_bytes)
        unit = units[0]
        for candidate in units:
            unit = candidate
            if size < 1024.0 or candidate == units[-1]:
                break
            size /= 1024.0
        if unit == "B":
            return f"{int(size)} {unit}"
        return f"{size:.2f} {unit}"
