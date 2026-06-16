"""GUI tabs."""

from amiibo_flipper.gui.tabs.batch_runner import BatchRunnerTab
from amiibo_flipper.gui.tabs.converter import ConverterTab
from amiibo_flipper.gui.tabs.dashboard import DashboardTab
from amiibo_flipper.gui.tabs.duplicates import DuplicatesTab
from amiibo_flipper.gui.tabs.settings_panel import SettingsTab
from amiibo_flipper.gui.tabs.watch_monitor import WatchTab

__all__ = [
	"ConverterTab",
	"BatchRunnerTab",
	"WatchTab",
	"DuplicatesTab",
	"DashboardTab",
	"SettingsTab",
]
