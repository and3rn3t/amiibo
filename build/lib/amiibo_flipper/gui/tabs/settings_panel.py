"""Settings tab for managing GUI defaults."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QLabel,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from amiibo_flipper.gui.settings import GuiSettings, load_settings, save_settings
from amiibo_flipper.gui.widgets import Card, LogViewer, PathSelector, section_title


class SettingsTab(QWidget):
    """Tab for editing GUI defaults used by other tabs."""

    settings_saved = pyqtSignal(object)  # GuiSettings

    def __init__(self):
        super().__init__()
        self._settings = load_settings()
        self._init_ui()
        self._apply_settings_to_controls(self._settings)

    @staticmethod
    def _card_layout(card: Card) -> QVBoxLayout:
        """Return a stable vertical layout for a Card."""
        existing_attr = getattr(card, "layout", None)
        if isinstance(existing_attr, QVBoxLayout):
            return existing_attr

        existing_callable = getattr(card, "layout", None)
        if callable(existing_callable):
            existing = existing_callable()
            if isinstance(existing, QVBoxLayout):
                return existing

        fallback = QVBoxLayout()
        card.setLayout(fallback)
        return fallback

    def _init_ui(self) -> None:
        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)

        converter_card = Card()
        converter_layout = self._card_layout(converter_card)
        converter_layout.addWidget(section_title("Converter Defaults"))

        self.converter_source_selector = PathSelector("Default Source:", is_directory=True)
        self.converter_output_selector = PathSelector("Default Output:", is_directory=True)
        self.converter_workers_spin = QSpinBox()
        self.converter_workers_spin.setMinimum(1)
        self.converter_workers_spin.setMaximum(16)
        self.converter_workers_spin.setValue(4)
        self.converter_overwrite_check = QCheckBox("Default overwrite")
        self.converter_flatten_check = QCheckBox("Default flatten")

        converter_layout.addWidget(self.converter_source_selector)
        converter_layout.addWidget(self.converter_output_selector)
        converter_layout.addWidget(QLabel("Default workers:"))
        converter_layout.addWidget(self.converter_workers_spin)
        converter_layout.addWidget(self.converter_overwrite_check)
        converter_layout.addWidget(self.converter_flatten_check)

        layout.addWidget(converter_card)

        watch_card = Card()
        watch_layout = self._card_layout(watch_card)
        watch_layout.addWidget(section_title("Watch Defaults"))

        self.watch_source_selector = PathSelector("Default Watch Source:", is_directory=True)
        self.watch_output_selector = PathSelector("Default Watch Output:", is_directory=True)
        self.watch_overwrite_check = QCheckBox("Default watch overwrite")
        self.watch_flatten_check = QCheckBox("Default watch flatten")

        watch_layout.addWidget(self.watch_source_selector)
        watch_layout.addWidget(self.watch_output_selector)
        watch_layout.addWidget(self.watch_overwrite_check)
        watch_layout.addWidget(self.watch_flatten_check)

        layout.addWidget(watch_card)

        batch_card = Card()
        batch_layout = self._card_layout(batch_card)
        batch_layout.addWidget(section_title("Batch Defaults"))

        self.batch_file_selector = PathSelector("Default Batch File:", is_directory=False)
        batch_layout.addWidget(self.batch_file_selector)

        self.save_btn = QPushButton("Save Settings")
        style = self.style()
        if style is not None:
            self.save_btn.setIcon(
                style.standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton)
            )
        self.save_btn.clicked.connect(self._on_save)
        batch_layout.addWidget(self.save_btn)

        layout.addWidget(batch_card)

        appearance_card = Card()
        appearance_layout = self._card_layout(appearance_card)
        appearance_layout.addWidget(section_title("Appearance"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["light", "dark"])
        self.compact_mode_check = QCheckBox("Compact mode")
        appearance_layout.addWidget(QLabel("Theme:"))
        appearance_layout.addWidget(self.theme_combo)
        appearance_layout.addWidget(self.compact_mode_check)

        layout.addWidget(appearance_card)

        log_card = Card()
        log_layout = self._card_layout(log_card)
        log_layout.addWidget(section_title("Settings Activity"))

        self.log_viewer = LogViewer()
        log_layout.addWidget(self.log_viewer, 1)

        self.log_viewer.setMinimumHeight(120)
        layout.addWidget(log_card)
        layout.addStretch(1)

        content.setLayout(layout)
        scroll.setWidget(content)
        root_layout.addWidget(scroll)
        self.setLayout(root_layout)

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
        self.theme_combo.setCurrentText(settings.theme if settings.theme in {"light", "dark"} else "light")
        self.compact_mode_check.setChecked(settings.compact_mode)

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
            theme=self.theme_combo.currentText(),
            compact_mode=self.compact_mode_check.isChecked(),
        )
        save_settings(settings)
        self._settings = settings
        self.settings_saved.emit(settings)
        self.log_viewer.append_log("Settings saved", "SUCCESS")
