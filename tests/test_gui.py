"""Tests for GUI components."""

import pytest
from PyQt6.QtWidgets import QApplication
from pathlib import Path

from amiibo_flipper.gui.widgets import PathSelector, LogViewer
from amiibo_flipper.gui.tabs import ConverterTab, BatchRunnerTab
from amiibo_flipper.gui.main_window import MainWindow


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class TestPathSelector:
    """Tests for PathSelector widget."""

    def test_path_selector_init_directory(self, qapp):
        """Test PathSelector initialization for directory selection."""
        selector = PathSelector(label="Test:", is_directory=True)
        assert selector.is_directory is True
        assert selector.get_path() == ""

    def test_path_selector_init_file(self, qapp):
        """Test PathSelector initialization for file selection."""
        selector = PathSelector(label="Test:", is_directory=False)
        assert selector.is_directory is False
        assert selector.get_path() == ""

    def test_path_selector_set_path(self, qapp):
        """Test setting path."""
        selector = PathSelector()
        test_path = "/tmp/test"
        selector.set_path(test_path)
        assert selector.get_path() == test_path


class TestLogViewer:
    """Tests for LogViewer widget."""

    def test_log_viewer_init(self, qapp):
        """Test LogViewer initialization."""
        viewer = LogViewer()
        assert viewer.isReadOnly() is True

    def test_log_viewer_append_info(self, qapp):
        """Test appending INFO log."""
        viewer = LogViewer()
        viewer.append_log("Test message", "INFO")
        assert "Test message" in viewer.toHtml()

    def test_log_viewer_append_error(self, qapp):
        """Test appending ERROR log."""
        viewer = LogViewer()
        viewer.append_log("Error occurred", "ERROR")
        assert "Error occurred" in viewer.toHtml()

    def test_log_viewer_clear(self, qapp):
        """Test clearing logs."""
        viewer = LogViewer()
        viewer.append_log("Message", "INFO")
        viewer.clear_logs()
        assert viewer.toPlainText() == ""


class TestConverterTab:
    """Tests for ConverterTab."""

    def test_converter_tab_init(self, qapp):
        """Test ConverterTab initialization."""
        tab = ConverterTab()
        assert tab.mode_combo is not None
        assert tab.source_selector is not None
        assert tab.output_selector is not None
        assert tab.convert_btn is not None

    def test_converter_tab_mode_change(self, qapp):
        """Test mode change enables/disables flatten option."""
        tab = ConverterTab()
        # Start with convert mode
        assert tab.flatten_check.isEnabled() is False
        # Change to archive mode
        tab.mode_combo.setCurrentText("Import archive")
        assert tab.flatten_check.isEnabled() is True
        # Change back to convert mode
        tab.mode_combo.setCurrentText("Convert .bin files")
        assert tab.flatten_check.isEnabled() is False

    def test_converter_tab_workers_range(self, qapp):
        """Test workers spin box range."""
        tab = ConverterTab()
        assert tab.workers_spin.minimum() == 1
        assert tab.workers_spin.maximum() == 16
        assert tab.workers_spin.value() == 4


class TestBatchRunnerTab:
    """Tests for BatchRunnerTab."""

    def test_batch_runner_tab_init(self, qapp):
        """Test BatchRunnerTab initialization."""
        tab = BatchRunnerTab()
        assert tab.file_selector is not None
        assert tab.run_btn is not None
        assert tab.log_viewer is not None

    def test_batch_runner_tab_file_selector(self, qapp):
        """Test file selector is for files, not directories."""
        tab = BatchRunnerTab()
        assert tab.file_selector.is_directory is False


class TestMainWindow:
    """Tests for MainWindow."""

    def test_main_window_init(self, qapp):
        """Test MainWindow initialization."""
        window = MainWindow()
        assert window.windowTitle() == "amiibo-flipper GUI"
        assert window.centralWidget() is not None

    def test_main_window_has_tabs(self, qapp):
        """Test MainWindow has converter and batch runner tabs."""
        window = MainWindow()
        central = window.centralWidget()
        assert central is not None
        # Find the tab widget
        from PyQt6.QtWidgets import QTabWidget
        tabs = None
        for widget in central.findChildren(QTabWidget):
            tabs = widget
            break
        assert tabs is not None
        assert tabs.count() == 2
