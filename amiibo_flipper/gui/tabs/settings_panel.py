"""Settings tab for managing GUI defaults."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QCheckBox,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from amiibo_flipper.gui.settings import GuiSettings, load_settings, save_settings
from amiibo_flipper.gui.widgets import LogViewer, PathSelector


class SettingsTab(QWidget):
    """Tab for editing GUI defaults used by other tabs."""

    def __init__(self):
        super().__init__()
        self._settings = load_settings()
        self._init_ui()
        self._apply_settings_to_controls(self._settings)

    def _init_ui(self) -> None:
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Converter Defaults"))
        self.converter_source_selector = PathSelector("Default Source:", is_directory=True)
        self.converter_output_selector = PathSelector("Default Output:", is_directory=True)
        self.converter_workers_spin = QSpinBox()
        self.converter_workers_spin.setMinimum(1)
        self.converter_workers_spin.setMaximum(16)
        self.converter_workers_spin.setValue(4)
        self.converter_overwrite_check = QCheckBox("Default overwrite")
        self.converter_flatten_check = QCheckBox("Default flatten")

        layout.addWidget(self.converter_source_selector)
        layout.addWidget(self.converter_output_selector)
        layout.addWidget(QLabel("Default workers:"))
        layout.addWidget(self.converter_workers_spin)
        layout.addWidget(self.converter_overwrite_check)
        layout.addWidget(self.converter_flatten_check)

        layout.addWidget(QLabel("Watch Defaults"))
        self.watch_source_selector = PathSelector("Default Watch Source:", is_directory=True)
        self.watch_output_selector = PathSelector("Default Watch Output:", is_directory=True)
        self.watch_overwrite_check = QCheckBox("Default watch overwrite")
        self.watch_flatten_check = QCheckBox("Default watch flatten")

        layout.addWidget(self.watch_source_selector)
        layout.addWidget(self.watch_output_selector)
        layout.addWidget(self.watch_overwrite_check)
        layout.addWidget(self.watch_flatten_check)

        layout.addWidget(QLabel("Batch Defaults"))
        self.batch_file_selector = PathSelector("Default Batch File:", is_directory=False)
        layout.addWidget(self.batch_file_selector)

        self.save_btn = QPushButton("Save Settings")
        self.save_btn.clicked.connect(self._on_save)
        layout.addWidget(self.save_btn)

        self.log_viewer = LogViewer()
        layout.addWidget(self.log_viewer, 1)

        self.setLayout(layout)

    def _apply_settings_to_controls(self, settings: GuiSettings) -> None:
        self.converter_source_selector.set_path(settings.converter_source_dir)
        self.converter_output_selector.set_path(settings.converter_output_dir)
        self.converter_workers_spin.setValue(settings.converter_workers)
        self.converter_overwrite_check.setChecked(settings.converter_overwrite)
        self.converter_flatten_check.setChecked(settings.converter_flatten)
        self.watch_source_selector.set_path(settings.watch_source_dir)
        self.watch_output_selector.set_path(settings.watch_output_dir)
        self.watch_overwrite_check.setChecked(settings.watch_overwrite)
        self.watch_flatten_check.setChecked(settings.watch_flatten)
        self.batch_file_selector.set_path(settings.batch_file)

    def _on_save(self) -> None:
        settings = GuiSettings(
            converter_source_dir=self.converter_source_selector.get_path().strip(),
            converter_output_dir=self.converter_output_selector.get_path().strip(),
            converter_workers=self.converter_workers_spin.value(),
            converter_overwrite=self.converter_overwrite_check.isChecked(),
            converter_flatten=self.converter_flatten_check.isChecked(),
            watch_source_dir=self.watch_source_selector.get_path().strip(),
            watch_output_dir=self.watch_output_selector.get_path().strip(),
            watch_overwrite=self.watch_overwrite_check.isChecked(),
            watch_flatten=self.watch_flatten_check.isChecked(),
            batch_file=self.batch_file_selector.get_path().strip(),
        )
        save_settings(settings)
        self.log_viewer.append_log("Settings saved", "SUCCESS")
