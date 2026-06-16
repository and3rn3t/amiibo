"""Tests for GUI components."""

import os
from pathlib import Path

import pytest
from PyQt6.QtWidgets import QApplication

if os.environ.get("AMIIBO_RUN_GUI_TESTS") != "1":
    pytest.skip(
        "GUI tests are opt-in; run with AMIIBO_RUN_GUI_TESTS=1 in a local GUI session",
        allow_module_level=True,
    )

from amiibo_flipper.gui.main_window import MainWindow
from amiibo_flipper.gui.tabs import BatchRunnerTab, ConverterTab
from amiibo_flipper.gui.tabs.dashboard import compute_dashboard_stats
from amiibo_flipper.gui.tabs.duplicates import DuplicatesTab
from amiibo_flipper.gui.tabs.settings_panel import SettingsTab
from amiibo_flipper.gui.tabs.watch_monitor import WatchTab
from amiibo_flipper.gui.widgets import PathSelector, LogViewer


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication for tests."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
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


class TestDuplicatesTab:
    """Tests for DuplicatesTab."""

    def test_duplicates_tab_init(self, qapp):
        """Test DuplicatesTab initialization."""
        tab = DuplicatesTab()
        assert tab.source_selector is not None
        assert tab.report_selector is not None
        assert tab.scan_btn is not None
        assert tab.save_report_check.isChecked() is False
        assert tab.report_selector.isEnabled() is False

    def test_duplicates_report_toggle(self, qapp):
        """Test enabling/disabling report output selection."""
        tab = DuplicatesTab()
        tab.save_report_check.setChecked(True)
        assert tab.report_selector.isEnabled() is True
        tab.save_report_check.setChecked(False)
        assert tab.report_selector.isEnabled() is False


class TestDashboardStats:
    """Tests for dashboard stat helpers."""

    def test_compute_dashboard_stats(self, tmp_path: Path):
        """Compute totals including duplicate groups."""
        source = tmp_path / "collection"
        source.mkdir()
        (source / "a.nfc").write_text("same", encoding="utf-8")
        (source / "b.nfc").write_text("same", encoding="utf-8")
        (source / "c.bin").write_bytes(b"abc")

        stats = compute_dashboard_stats(source)

        assert stats.total_files == 3
        assert stats.nfc_files == 2
        assert stats.bin_files == 1
        assert stats.duplicate_files == 1
        assert stats.duplicate_groups == 1
        assert stats.total_bytes > 0


class TestWatchTab:
    """Tests for WatchTab."""

    def test_watch_tab_init(self, qapp):
        """Watch tab should initialize controls and counters."""
        tab = WatchTab()
        assert tab.source_selector is not None
        assert tab.output_selector is not None
        assert tab.start_btn.isEnabled() is True
        assert tab.stop_btn.isEnabled() is False
        assert tab.converted_label.text() == "Converted: 0"

    def test_watch_tab_running_ui_toggle(self, qapp):
        """Start/stop button states should toggle with run state."""
        tab = WatchTab()
        tab._set_running_ui(True)
        assert tab.start_btn.isEnabled() is False
        assert tab.stop_btn.isEnabled() is True
        tab._set_running_ui(False)
        assert tab.start_btn.isEnabled() is True
        assert tab.stop_btn.isEnabled() is False


class TestSettingsTab:
    """Tests for SettingsTab."""

    def test_settings_tab_init(self, qapp):
        """Settings tab should expose save controls."""
        tab = SettingsTab()
        assert tab.save_btn is not None
        assert tab.converter_workers_spin.value() >= 1


class TestMainWindow:
    """Tests for MainWindow."""

    def test_main_window_init(self, qapp):
        """Test MainWindow initialization."""
        window = MainWindow()
        assert window.windowTitle() == "amiibo-flipper GUI"
        assert window.centralWidget() is not None

    def test_main_window_has_tabs(self, qapp):
        """Test MainWindow has all feature tabs."""
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
        assert tabs.count() == 6
