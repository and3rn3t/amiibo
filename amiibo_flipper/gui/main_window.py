"""Main GUI window."""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget

from amiibo_flipper.gui.tabs import (
    BatchRunnerTab,
    ConverterTab,
    DashboardTab,
    DuplicatesTab,
    WatchTab,
)

logger = logging.getLogger(__name__)


def _configure_qt_plugin_paths() -> None:
    """Set Qt plugin locations explicitly for venv-based installs on macOS."""
    try:
        import PyQt6
    except Exception:
        return

    pyqt_root = Path(PyQt6.__file__).resolve().parent
    plugin_root = pyqt_root / "Qt6" / "plugins"
    platform_root = plugin_root / "platforms"

    if plugin_root.exists():
        os.environ.setdefault("QT_PLUGIN_PATH", str(plugin_root))
    if platform_root.exists():
        os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", str(platform_root))


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        """Initialize main window."""
        super().__init__()
        self.setWindowTitle("amiibo-flipper GUI")
        self.setGeometry(100, 100, 1000, 600)
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI."""
        central_widget = QWidget()
        layout = QVBoxLayout()

        # Create tabs
        tabs = QTabWidget()
        tabs.addTab(ConverterTab(), "Converter")
        tabs.addTab(BatchRunnerTab(), "Batch Runner")
        tabs.addTab(WatchTab(), "Watch")
        tabs.addTab(DuplicatesTab(), "Duplicates")
        tabs.addTab(DashboardTab(), "Dashboard")

        layout.addWidget(tabs)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)


def main() -> None:
    """Entry point for GUI application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    _configure_qt_plugin_paths()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
