"""Main GUI window."""

import logging
import os
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget

from amiibo_flipper.gui.tabs import (
    BatchRunnerTab,
    ConverterTab,
    DashboardTab,
    DuplicatesTab,
    SettingsTab,
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
        self.converter_tab = ConverterTab()
        self.batch_tab = BatchRunnerTab()
        self.watch_tab = WatchTab()
        self.duplicates_tab = DuplicatesTab()
        self.dashboard_tab = DashboardTab()
        self.settings_tab = SettingsTab()

        tabs.addTab(self.converter_tab, "Converter")
        tabs.addTab(self.batch_tab, "Batch Runner")
        tabs.addTab(self.watch_tab, "Watch")
        tabs.addTab(self.duplicates_tab, "Duplicates")
        tabs.addTab(self.dashboard_tab, "Dashboard")
        tabs.addTab(self.settings_tab, "Settings")

        self.settings_tab.settings_saved.connect(self._on_settings_saved)

        layout.addWidget(tabs)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def _on_settings_saved(self, settings: object) -> None:
        """Apply newly saved defaults to already-open tabs."""
        self.converter_tab.apply_settings(settings)
        self.batch_tab.apply_settings(settings)
        self.watch_tab.apply_settings(settings)


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
