"""Reusable GUI components."""

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QWidget,
)


class PathSelector(QWidget):
    """Widget for selecting file/directory paths."""

    def __init__(self, label: str = "Path:", is_directory: bool = True):
        """Initialize path selector.
        
        Args:
            label: Label text
            is_directory: If True, select directories; if False, select files
        """
        super().__init__()
        self.is_directory = is_directory
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.label = QLabel(label)
        self.path_input = QLineEdit()
        self.path_input.setReadOnly(True)
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._on_browse)
        
        layout.addWidget(self.label)
        layout.addWidget(self.path_input, 1)
        layout.addWidget(self.browse_btn)
        
        self.setLayout(layout)
    
    def _on_browse(self) -> None:
        """Open file/directory dialog."""
        if self.is_directory:
            path = QFileDialog.getExistingDirectory(
                self,
                "Select Directory",
                str(Path.home()),
            )
        else:
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Select File",
                str(Path.home()),
            )
        
        if path:
            self.set_path(path)
    
    def set_path(self, path: str) -> None:
        """Set the selected path."""
        self.path_input.setText(path)
    
    def get_path(self) -> str:
        """Get the selected path."""
        return self.path_input.text()


class LogViewer(QTextEdit):
    """Widget for displaying log output."""

    def __init__(self):
        """Initialize log viewer."""
        super().__init__()
        self.setReadOnly(True)
        self.setStyleSheet(
            "QTextEdit { background-color: #1e1e1e; color: #d4d4d4; font-family: Menlo, Monaco, 'Courier New', monospace; }"
        )
    
    def append_log(self, message: str, level: str = "INFO") -> None:
        """Append a log message.
        
        Args:
            message: The message to log
            level: Log level (INFO, ERROR, WARNING, SUCCESS)
        """
        colors = {
            "INFO": "#569cd6",
            "ERROR": "#f48771",
            "WARNING": "#dcdcaa",
            "SUCCESS": "#6a9955",
        }
        color = colors.get(level, colors["INFO"])
        
        timestamp = ""  # Could add timestamp with datetime.now().strftime("%H:%M:%S")
        formatted = f'<span style="color: {color};">[{level}] {message}</span>'
        
        self.append(formatted)
    
    def clear_logs(self) -> None:
        """Clear all logs."""
        self.clear()
