"""Reusable GUI components."""

from pathlib import Path

from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
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
        self.browse_btn.setProperty("variant", "secondary")
        self.browse_btn.setMinimumWidth(96)
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
        self.setObjectName("LogViewer")
    
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
        
        formatted = f'<span style="color: {color};">[{level}] {message}</span>'
        
        self.append(formatted)
    
    def clear_logs(self) -> None:
        """Clear all logs."""
        self.clear()


class Card(QFrame):
    """Simple card container used to visually group controls."""

    def __init__(self):
        super().__init__()
        self.setObjectName("Card")
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(14, 14, 14, 14)
        self.layout.setSpacing(10)
        self.setLayout(self.layout)


def section_title(text: str) -> QLabel:
    """Styled section title label."""
    label = QLabel(text)
    label.setObjectName("SectionTitle")
    return label
