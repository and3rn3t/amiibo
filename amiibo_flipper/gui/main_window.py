"""Main GUI window."""

import logging
import os
import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QTabWidget, QVBoxLayout, QWidget

from amiibo_flipper.gui.tabs import (
    BatchRunnerTab,
    ConverterTab,
    DashboardTab,
    DuplicatesTab,
    SettingsTab,
    WatchTab,
)

logger = logging.getLogger(__name__)


APP_STYLE = """
QWidget {
    background: #f3efe7;
    color: #1f2a30;
    font-family: Avenir Next, Helvetica Neue, Helvetica, Arial, sans-serif;
    font-size: 13px;
}

QLabel#AppTitle {
    font-size: 24px;
    font-weight: 700;
    color: #102129;
    margin-bottom: 2px;
}

QLabel#AppSubtitle {
    font-size: 12px;
    color: #566973;
    margin-bottom: 8px;
}

QLabel#SectionTitle {
    font-size: 14px;
    font-weight: 700;
    color: #173645;
}

QFrame#Card {
    background: #fffdf9;
    border: 1px solid #ded6c7;
    border-radius: 10px;
}

QTabWidget::pane {
    border: 1px solid #d9d1c2;
    border-radius: 10px;
    background: #fffdf9;
    top: -1px;
}

QTabBar::tab {
    background: #ece6da;
    border: 1px solid #d9d1c2;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 8px 14px;
    margin-right: 4px;
    color: #415560;
}

QTabBar::tab:selected {
    background: #fffdf9;
    color: #163845;
    font-weight: 600;
}

QLineEdit, QComboBox, QSpinBox, QTextEdit {
    background: #ffffff;
    border: 1px solid #cfc6b8;
    border-radius: 8px;
    padding: 6px 8px;
}

QPushButton {
    background: #26556a;
    color: #f8fafb;
    border: none;
    border-radius: 8px;
    padding: 8px 12px;
    font-weight: 600;
}

QPushButton:hover {
    background: #2f6880;
}

QPushButton:pressed {
    background: #1f4455;
}

QPushButton:disabled {
    background: #99a8b0;
    color: #edf1f3;
}

QProgressBar {
    border: 1px solid #cfc6b8;
    border-radius: 8px;
    background: #f7f3eb;
    text-align: center;
}

QProgressBar::chunk {
    border-radius: 7px;
    background: #3d8a83;
}
"""


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
        self.setMinimumSize(1060, 720)
        self.setGeometry(100, 100, 1160, 780)
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI."""
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 12, 16, 16)
        layout.setSpacing(10)

        title = QLabel("amiibo-flipper")
        title.setObjectName("AppTitle")
        subtitle = QLabel("Convert, monitor, and manage your amiibo workflows from one place")
        subtitle.setObjectName("AppSubtitle")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Create tabs
        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.setElideMode(Qt.TextElideMode.ElideRight)
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
    app.setStyleSheet(APP_STYLE)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
