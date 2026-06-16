"""Main GUI window."""

import logging
import sys
from typing import Optional

from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget

from amiibo_flipper.gui.tabs import ConverterTab, BatchRunnerTab

logger = logging.getLogger(__name__)


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

        layout.addWidget(tabs)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)


def main() -> None:
    """Entry point for GUI application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
