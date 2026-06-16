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
            "muted_fg": "#d5e0e5",
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
            "log_bg": "#111b20",
            "log_border": "#2a414a",
            "log_text": "#d4dde1",
            "focus": "#4ea2b4",
            "scroll_track": "#102028",
            "scroll_thumb": "#2c6674",
            "scroll_thumb_hover": "#378096",
        }
    else:
        palette = {
            "bg": "#f3efe7",
            "fg": "#1f2a30",
            "muted_fg": "#334750",
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
            "log_bg": "#f9f6ef",
            "log_border": "#d8cfbf",
            "log_text": "#33464f",
            "focus": "#2f6880",
            "scroll_track": "#ebe5d9",
            "scroll_thumb": "#9eb2bb",
            "scroll_thumb_hover": "#819ca7",
        }

    font_size = "12px" if compact_mode else "13px"
    tab_padding = "6px 10px" if compact_mode else "8px 14px"
    input_padding = "4px 6px" if compact_mode else "6px 8px"
    button_padding = "6px 10px" if compact_mode else "8px 12px"

    return f"""
QMainWindow {{
    background: {palette['bg']};
}}

QWidget {{
    background: transparent;
    color: {palette['fg']};
    font-family: Avenir Next, Helvetica Neue, Helvetica, Arial, sans-serif;
    font-size: {font_size};
}}

QWidget#MainRoot {{
    background: qlineargradient(
        x1: 0,
        y1: 0,
        x2: 0,
        y2: 1,
        stop: 0 {palette['bg']},
        stop: 1 {palette['pane_bg']}
    );
}}

QScrollArea {{
    background: transparent;
    border: none;
}}

QScrollArea > QWidget > QWidget {{
    background: transparent;
}}

QLabel {{
    min-height: 18px;
    background: transparent;
    color: {palette['muted_fg']};
}}

QCheckBox {{
    background: transparent;
    color: {palette['muted_fg']};
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

QFrame#Card:hover {{
    border: 1px solid {palette['focus']};
}}

QTabWidget::pane {{
    border: 1px solid {palette['pane_border']};
    border-radius: 10px;
    background: {palette['pane_bg']};
    margin-top: 0px;
}}

QTabWidget::tab-bar {{
    alignment: left;
}}

QTabBar {{
    background: transparent;
}}

QTabBar::tab {{
    background: {palette['tab_bg']};
    border: 1px solid {palette['pane_border']};
    border-bottom: 1px solid {palette['pane_border']};
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: {tab_padding};
    margin-right: 2px;
    min-height: 22px;
    color: {palette['tab_fg']};
}}

QTabBar::tab:selected {{
    background: {palette['tab_selected']};
    border-bottom: 1px solid {palette['tab_selected']};
    color: {palette['tab_selected_fg']};
    font-weight: 600;
}}

QTabBar::tab:hover:!selected {{
    background: {palette['tab_selected']};
}}

QLineEdit, QComboBox, QSpinBox, QTextEdit {{
    background: {palette['input_bg']};
    border: 1px solid {palette['input_border']};
    border-radius: 8px;
    padding: {input_padding};
}}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTextEdit:focus {{
    border: 1px solid {palette['focus']};
}}

QLineEdit, QComboBox, QSpinBox {{
    min-height: 28px;
}}

QCheckBox {{
    min-height: 22px;
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
}}

QCheckBox::indicator:unchecked {{
    background: {palette['input_bg']};
    border: 1px solid {palette['input_border']};
    border-radius: 5px;
}}

QCheckBox::indicator:checked {{
    background: {palette['button_bg']};
    border: 1px solid {palette['button_bg']};
    border-radius: 5px;
}}

QPushButton {{
    background: {palette['button_bg']};
    color: #f8fafb;
    border: none;
    border-radius: 8px;
    padding: {button_padding};
    min-height: 30px;
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

QPushButton[variant="secondary"] {{
    background: transparent;
    border: 1px solid {palette['input_border']};
    color: {palette['muted_fg']};
}}

QPushButton[variant="secondary"]:hover {{
    background: {palette['tab_bg']};
    border: 1px solid {palette['focus']};
}}

QPushButton[variant="danger"] {{
    background: transparent;
    border: 1px solid #9f4a4a;
    color: #e7b5b5;
}}

QPushButton[variant="danger"]:hover {{
    background: #6f2f2f;
    color: #ffe7e7;
}}

QComboBox::drop-down, QSpinBox::up-button, QSpinBox::down-button {{
    border: none;
    background: transparent;
    width: 18px;
}}

QComboBox::down-arrow {{
    width: 10px;
    height: 10px;
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

QTextEdit#LogViewer {{
    background: {palette['log_bg']};
    color: {palette['log_text']};
    border: 1px solid {palette['log_border']};
    border-radius: 8px;
    font-family: Menlo, Monaco, 'Courier New', monospace;
}}

QScrollBar:vertical {{
    background: {palette['scroll_track']};
    width: 12px;
    margin: 6px 2px 6px 2px;
    border-radius: 6px;
}}

QScrollBar::handle:vertical {{
    background: {palette['scroll_thumb']};
    min-height: 28px;
    border-radius: 6px;
}}

QScrollBar::handle:vertical:hover {{
    background: {palette['scroll_thumb_hover']};
}}

QScrollBar:horizontal {{
    background: {palette['scroll_track']};
    height: 12px;
    margin: 2px 6px 2px 6px;
    border-radius: 6px;
}}

QScrollBar::handle:horizontal {{
    background: {palette['scroll_thumb']};
    min-width: 28px;
    border-radius: 6px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {palette['scroll_thumb_hover']};
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical,
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    border: none;
    background: transparent;
    width: 0px;
    height: 0px;
}}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical,
QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {{
    background: transparent;
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
        central_widget.setObjectName("MainRoot")
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
        tabs.setDocumentMode(False)
        tab_bar = tabs.tabBar()
        if tab_bar is not None:
            tab_bar.setExpanding(False)
            tab_bar.setUsesScrollButtons(True)
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

        style = self.style()
        if style is not None:
            tabs.setTabIcon(0, style.standardIcon(QStyle.StandardPixmap.SP_CommandLink))
            tabs.setTabIcon(1, style.standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
            tabs.setTabIcon(2, style.standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
            tabs.setTabIcon(3, style.standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton))
            tabs.setTabIcon(4, style.standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
            tabs.setTabIcon(5, style.standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView))

        self.settings_tab.settings_saved.connect(self._on_settings_saved)

        layout.addWidget(tabs)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def _on_settings_saved(self, settings: object) -> None:
        """Apply newly saved defaults to already-open tabs."""
        if not isinstance(settings, GuiSettings):
            return
        self._settings = settings
        self.converter_tab.apply_settings(settings)
        self.batch_tab.apply_settings(settings)
        self.watch_tab.apply_settings(settings)
        self._apply_theme_and_density(settings)

    def _apply_theme_and_density(self, settings: GuiSettings) -> None:
        """Apply theme and compact mode to the running app."""
        app = QApplication.instance()
        if not isinstance(app, QApplication):
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
