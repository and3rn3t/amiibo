"""Main GUI window."""

import logging
import os
import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QStyle,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from amiibo_flipper.gui.settings import GuiSettings, load_settings
from amiibo_flipper.gui.tabs import (
    BatchRunnerTab,
    ConverterTab,
    DashboardTab,
    DuplicatesTab,
    SettingsTab,
    WatchTab,
)

logger = logging.getLogger(__name__)


def build_app_style(theme: str, compact_mode: bool) -> str:
    """Build stylesheet for selected theme and density."""
    if theme == "dark":
        palette = {
            "bg": "#0f171b",
            "fg": "#e9eef0",
            "title": "#f4f7f8",
            "subtitle": "#9fb2bb",
            "section": "#8fc4d5",
            "card_bg": "#162329",
            "card_border": "#29414a",
            "pane_border": "#2d434c",
            "pane_bg": "#162329",
            "tab_bg": "#203238",
            "tab_selected": "#162329",
            "tab_fg": "#a8bbc3",
            "tab_selected_fg": "#eaf1f4",
            "input_bg": "#1d2e35",
            "input_border": "#35505a",
            "button_bg": "#2f7b8a",
            "button_hover": "#3d96a8",
            "button_pressed": "#245f6a",
            "button_disabled_bg": "#51656d",
            "button_disabled_fg": "#ced7dc",
            "progress_bg": "#1e2e34",
            "progress_chunk": "#4da394",
        }
    else:
        palette = {
            "bg": "#f3efe7",
            "fg": "#1f2a30",
            "title": "#102129",
            "subtitle": "#566973",
            "section": "#173645",
            "card_bg": "#fffdf9",
            "card_border": "#ded6c7",
            "pane_border": "#d9d1c2",
            "pane_bg": "#fffdf9",
            "tab_bg": "#ece6da",
            "tab_selected": "#fffdf9",
            "tab_fg": "#415560",
            "tab_selected_fg": "#163845",
            "input_bg": "#ffffff",
            "input_border": "#cfc6b8",
            "button_bg": "#26556a",
            "button_hover": "#2f6880",
            "button_pressed": "#1f4455",
            "button_disabled_bg": "#99a8b0",
            "button_disabled_fg": "#edf1f3",
            "progress_bg": "#f7f3eb",
            "progress_chunk": "#3d8a83",
        }

    font_size = "12px" if compact_mode else "13px"
    tab_padding = "6px 10px" if compact_mode else "8px 14px"
    input_padding = "4px 6px" if compact_mode else "6px 8px"
    button_padding = "6px 10px" if compact_mode else "8px 12px"

    return f"""
QWidget {{
    background: {palette['bg']};
    color: {palette['fg']};
    font-family: Avenir Next, Helvetica Neue, Helvetica, Arial, sans-serif;
    font-size: {font_size};
}}

QLabel#AppTitle {{
    font-size: 24px;
    font-weight: 700;
    color: {palette['title']};
    margin-bottom: 2px;
}}

QLabel#AppSubtitle {{
    font-size: 12px;
    color: {palette['subtitle']};
    margin-bottom: 8px;
}}

QLabel#SectionTitle {{
    font-size: 14px;
    font-weight: 700;
    color: {palette['section']};
}}

QFrame#Card {{
    background: {palette['card_bg']};
    border: 1px solid {palette['card_border']};
    border-radius: 10px;
}}

QTabWidget::pane {{
    border: 1px solid {palette['pane_border']};
    border-radius: 10px;
    background: {palette['pane_bg']};
    top: -1px;
}}

QTabBar::tab {{
    background: {palette['tab_bg']};
    border: 1px solid {palette['pane_border']};
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: {tab_padding};
    margin-right: 4px;
    color: {palette['tab_fg']};
}}

QTabBar::tab:selected {{
    background: {palette['tab_selected']};
    color: {palette['tab_selected_fg']};
    font-weight: 600;
}}

QLineEdit, QComboBox, QSpinBox, QTextEdit {{
    background: {palette['input_bg']};
    border: 1px solid {palette['input_border']};
    border-radius: 8px;
    padding: {input_padding};
}}

QPushButton {{
    background: {palette['button_bg']};
    color: #f8fafb;
    border: none;
    border-radius: 8px;
    padding: {button_padding};
    font-weight: 600;
}}

QPushButton:hover {{
    background: {palette['button_hover']};
}}

QPushButton:pressed {{
    background: {palette['button_pressed']};
}}

QPushButton:disabled {{
    background: {palette['button_disabled_bg']};
    color: {palette['button_disabled_fg']};
}}

QProgressBar {{
    border: 1px solid {palette['input_border']};
    border-radius: 8px;
    background: {palette['progress_bg']};
    text-align: center;
}}

QProgressBar::chunk {{
    border-radius: 7px;
    background: {palette['progress_chunk']};
}}
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
        self._settings = load_settings()
        self.setWindowTitle("amiibo-flipper GUI")
        self.setMinimumSize(1060, 720)
        self.setGeometry(100, 100, 1160, 780)
        self._init_ui()
        self._apply_theme_and_density(self._settings)

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

        tabs.setTabIcon(0, self.style().standardIcon(QStyle.StandardPixmap.SP_CommandLink))
        tabs.setTabIcon(1, self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
        tabs.setTabIcon(2, self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        tabs.setTabIcon(3, self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton))
        tabs.setTabIcon(4, self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
        tabs.setTabIcon(5, self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView))

        self.settings_tab.settings_saved.connect(self._on_settings_saved)

        layout.addWidget(tabs)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def _on_settings_saved(self, settings: object) -> None:
        """Apply newly saved defaults to already-open tabs."""
        self._settings = settings
        self.converter_tab.apply_settings(settings)
        self.batch_tab.apply_settings(settings)
        self.watch_tab.apply_settings(settings)
        self._apply_theme_and_density(settings)

    def _apply_theme_and_density(self, settings: GuiSettings) -> None:
        """Apply theme and compact mode to the running app."""
        app = QApplication.instance()
        if app is None:
            return
        app.setStyleSheet(build_app_style(settings.theme, settings.compact_mode))


def main() -> None:
    """Entry point for GUI application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    _configure_qt_plugin_paths()
    app = QApplication(sys.argv)
    initial = load_settings()
    app.setStyleSheet(build_app_style(initial.theme, initial.compact_mode))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
