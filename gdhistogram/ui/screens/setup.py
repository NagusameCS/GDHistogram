"""Setup screen - OAuth client configuration."""

from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog,
    QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

from gdhistogram.ui.widgets import (
    StyledButton, Card, StatusIndicator, 
    InstructionPanel, SectionHeader, ErrorPanel
)
from gdhistogram.auth.oauth_manager import OAuthManager


class SetupScreen(QWidget):
    """
    Screen 2 - API Credential Setup
    
    User selects their own OAuth client JSON file.
    """
    
    credentials_configured = Signal(str)  # Emits path to credentials file
    back_clicked = Signal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self._selected_file: Optional[Path] = None
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Header
        header = SectionHeader(
            "API Credential Setup",
            "Configure your own Google Cloud credentials for secure access."
        )
        layout.addWidget(header)
        
        # Instructions card
        instructions_card = Card()
        
        instructions_title = QLabel("Setup Instructions")
        instructions_title.setStyleSheet("color: #1F2937; font-size: 16px; font-weight: bold;")
        instructions_card.layout.addWidget(instructions_title)
        
        instructions = InstructionPanel()
        instructions.set_instructions([
            "Create a Google Cloud Project at console.cloud.google.com",
            "Enable Google Drive API and Google Docs API",
            "Go to APIs & Services → Credentials",
            "Create OAuth Client ID (select 'Desktop' as application type)",
            "Download the client_secret.json file",
            "Select the downloaded file below"
        ])
        instructions_card.layout.addWidget(instructions)
        
        layout.addWidget(instructions_card)
        
        # File selection card
        file_card = Card()
        
        file_title = QLabel("OAuth Client File")
        file_title.setStyleSheet("color: #1F2937; font-size: 16px; font-weight: bold;")
        file_card.layout.addWidget(file_title)
        
        # File selector row
        file_row = QHBoxLayout()
        
        self.file_label = QLabel("No file selected")
        self.file_label.setStyleSheet("color: #6B7280; font-size: 14px;")
        file_row.addWidget(self.file_label)
        
        file_row.addStretch()
        
        select_button = StyledButton("Select File", primary=False)
        select_button.clicked.connect(self._on_select_file)
        file_row.addWidget(select_button)
        
        file_card.layout.addLayout(file_row)
        
        # Status indicator
        self.status = StatusIndicator()
        file_card.layout.addWidget(self.status)
        
        # Error panel
        self.error_panel = ErrorPanel()
        self.error_panel.retry_requested.connect(self._on_select_file)
        file_card.layout.addWidget(self.error_panel)
        
        layout.addWidget(file_card)
        
        layout.addStretch()
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        
        back_button = StyledButton("Back", primary=False)
        back_button.clicked.connect(self.back_clicked.emit)
        nav_layout.addWidget(back_button)
        
        nav_layout.addStretch()
        
        self.continue_button = StyledButton("Continue", primary=True)
        self.continue_button.setEnabled(False)
        self.continue_button.clicked.connect(self._on_continue)
        nav_layout.addWidget(self.continue_button)
        
        layout.addLayout(nav_layout)
    
    def _on_select_file(self) -> None:
        """Handle file selection."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select OAuth Client JSON",
            str(Path.home()),
            "JSON Files (*.json)"
        )
        
        if not file_path:
            return
        
        self._validate_file(Path(file_path))
    
    def _validate_file(self, file_path: Path) -> None:
        """Validate the selected file."""
        self.error_panel.clear()
        
        is_valid, message, client_info = OAuthManager.validate_client_secrets(file_path)
        
        if is_valid:
            self._selected_file = file_path
            self.file_label.setText(file_path.name)
            self.status.set_success(f"Valid: {client_info.project_id}")
            self.continue_button.setEnabled(True)
        else:
            self._selected_file = None
            self.file_label.setText("Invalid file")
            self.status.set_error("Validation failed")
            self.error_panel.show_error(
                "Invalid OAuth Client File",
                message,
                "Make sure you selected the correct client_secret.json file from Google Cloud Console."
            )
            self.continue_button.setEnabled(False)
    
    def _on_continue(self) -> None:
        """Handle continue button click."""
        if self._selected_file:
            self.credentials_configured.emit(str(self._selected_file))
