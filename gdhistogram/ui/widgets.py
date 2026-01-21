"""Common UI widgets for GDHistogram."""

from typing import Optional, Callable
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QProgressBar, QSizePolicy, QSpacerItem
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class StyledButton(QPushButton):
    """A styled button with consistent appearance."""
    
    def __init__(
        self,
        text: str,
        primary: bool = True,
        parent: Optional[QWidget] = None
    ):
        super().__init__(text, parent)
        
        self.primary = primary
        self._apply_style()
    
    def _apply_style(self) -> None:
        """Apply button styling."""
        if self.primary:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #2563EB;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 14px;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background-color: #1D4ED8;
                }
                QPushButton:pressed {
                    background-color: #1E40AF;
                }
                QPushButton:disabled {
                    background-color: #9CA3AF;
                    color: #E5E7EB;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #2563EB;
                    border: 2px solid #2563EB;
                    padding: 12px 24px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 14px;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background-color: #EFF6FF;
                }
                QPushButton:pressed {
                    background-color: #DBEAFE;
                }
                QPushButton:disabled {
                    border-color: #9CA3AF;
                    color: #9CA3AF;
                }
            """)


class StatusIndicator(QWidget):
    """A status indicator with icon and text."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(16, 16)
        layout.addWidget(self.icon_label)
        
        self.text_label = QLabel()
        self.text_label.setStyleSheet("color: #6B7280; font-size: 13px;")
        layout.addWidget(self.text_label)
        
        layout.addStretch()
        
        self.set_neutral("Ready")
    
    def set_success(self, text: str) -> None:
        """Set success state."""
        self.icon_label.setStyleSheet("""
            background-color: #059669;
            border-radius: 8px;
        """)
        self.text_label.setText(text)
        self.text_label.setStyleSheet("color: #059669; font-size: 13px;")
    
    def set_error(self, text: str) -> None:
        """Set error state."""
        self.icon_label.setStyleSheet("""
            background-color: #DC2626;
            border-radius: 8px;
        """)
        self.text_label.setText(text)
        self.text_label.setStyleSheet("color: #DC2626; font-size: 13px;")
    
    def set_warning(self, text: str) -> None:
        """Set warning state."""
        self.icon_label.setStyleSheet("""
            background-color: #D97706;
            border-radius: 8px;
        """)
        self.text_label.setText(text)
        self.text_label.setStyleSheet("color: #D97706; font-size: 13px;")
    
    def set_neutral(self, text: str) -> None:
        """Set neutral state."""
        self.icon_label.setStyleSheet("""
            background-color: #9CA3AF;
            border-radius: 8px;
        """)
        self.text_label.setText(text)
        self.text_label.setStyleSheet("color: #6B7280; font-size: 13px;")
    
    def set_loading(self, text: str) -> None:
        """Set loading state."""
        self.icon_label.setStyleSheet("""
            background-color: #2563EB;
            border-radius: 8px;
        """)
        self.text_label.setText(text)
        self.text_label.setStyleSheet("color: #2563EB; font-size: 13px;")


class Card(QFrame):
    """A card container with consistent styling."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
            }
        """)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 24, 24, 24)
        self.layout.setSpacing(16)


class SectionHeader(QWidget):
    """A section header with title and optional description."""
    
    def __init__(
        self,
        title: str,
        description: Optional[str] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Title
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #1F2937;")
        layout.addWidget(title_label)
        
        # Description
        if description:
            desc_label = QLabel(description)
            desc_label.setStyleSheet("color: #6B7280; font-size: 14px;")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)


class ProgressPanel(QWidget):
    """A progress panel with step name and progress bar."""
    
    cancel_requested = Signal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Step label
        self.step_label = QLabel("Initializing...")
        self.step_label.setStyleSheet("color: #1F2937; font-size: 14px; font-weight: bold;")
        layout.addWidget(self.step_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: #E5E7EB;
                height: 8px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #2563EB;
                border-radius: 4px;
            }
        """)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status and cancel row
        status_row = QHBoxLayout()
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #6B7280; font-size: 13px;")
        status_row.addWidget(self.status_label)
        
        status_row.addStretch()
        
        self.cancel_button = StyledButton("Cancel", primary=False)
        self.cancel_button.clicked.connect(self.cancel_requested.emit)
        status_row.addWidget(self.cancel_button)
        
        layout.addLayout(status_row)
    
    def set_step(self, step: str) -> None:
        """Set current step name."""
        self.step_label.setText(step)
    
    def set_progress(self, current: int, total: int) -> None:
        """Set progress values."""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_label.setText(f"{current} / {total}")
    
    def set_indeterminate(self) -> None:
        """Set indeterminate progress."""
        self.progress_bar.setMaximum(0)
        self.progress_bar.setValue(0)
        self.status_label.setText("Processing...")
    
    def set_complete(self) -> None:
        """Set complete state."""
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(100)
        self.status_label.setText("Complete")
        self.cancel_button.setEnabled(False)


class ErrorPanel(QWidget):
    """An error display panel."""
    
    retry_requested = Signal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.setStyleSheet("""
            QWidget {
                background-color: #FEF2F2;
                border: 1px solid #FECACA;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        # Error title
        title_layout = QHBoxLayout()
        
        error_icon = QLabel("⚠")
        error_icon.setStyleSheet("color: #DC2626; font-size: 18px;")
        title_layout.addWidget(error_icon)
        
        self.title_label = QLabel("Error")
        self.title_label.setStyleSheet("color: #DC2626; font-weight: bold; font-size: 14px;")
        title_layout.addWidget(self.title_label)
        
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        
        # Error message
        self.message_label = QLabel("")
        self.message_label.setStyleSheet("color: #7F1D1D; font-size: 13px;")
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)
        
        # Action suggestion
        self.action_label = QLabel("")
        self.action_label.setStyleSheet("color: #991B1B; font-size: 13px;")
        self.action_label.setWordWrap(True)
        layout.addWidget(self.action_label)
        
        # Retry button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.retry_button = StyledButton("Retry", primary=False)
        self.retry_button.clicked.connect(self.retry_requested.emit)
        button_layout.addWidget(self.retry_button)
        
        layout.addLayout(button_layout)
        
        self.hide()
    
    def show_error(
        self,
        title: str,
        message: str,
        action: Optional[str] = None,
        show_retry: bool = True
    ) -> None:
        """Display an error."""
        self.title_label.setText(title)
        self.message_label.setText(message)
        
        if action:
            self.action_label.setText(action)
            self.action_label.show()
        else:
            self.action_label.hide()
        
        self.retry_button.setVisible(show_retry)
        self.show()
    
    def clear(self) -> None:
        """Clear and hide the error panel."""
        self.hide()


class InstructionPanel(QWidget):
    """A panel for displaying step-by-step instructions."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.setStyleSheet("""
            QWidget {
                background-color: #F0F9FF;
                border: 1px solid #BAE6FD;
                border-radius: 8px;
            }
        """)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 16, 16, 16)
        self.layout.setSpacing(8)
    
    def set_instructions(self, instructions: list[str]) -> None:
        """Set the list of instructions."""
        # Clear existing
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        for i, instruction in enumerate(instructions, 1):
            item = QLabel(f"{i}. {instruction}")
            item.setStyleSheet("color: #0C4A6E; font-size: 13px;")
            item.setWordWrap(True)
            self.layout.addWidget(item)
