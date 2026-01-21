"""Auth screen - OAuth authorization flow."""

from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Signal, Qt, QThread, QObject
from PySide6.QtGui import QFont

from gdhistogram.ui.widgets import (
    StyledButton, Card, StatusIndicator, 
    SectionHeader, ErrorPanel
)
from gdhistogram.auth.oauth_manager import OAuthManager


class AuthWorker(QObject):
    """Worker for running OAuth flow in background thread."""
    
    finished = Signal(bool)
    progress = Signal(str)
    
    def __init__(self, oauth_manager: OAuthManager):
        super().__init__()
        self.oauth_manager = oauth_manager
    
    def run(self) -> None:
        """Run the OAuth flow."""
        try:
            success = self.oauth_manager.run_oauth_flow(
                progress_callback=self.progress.emit
            )
            self.finished.emit(success)
        except Exception as e:
            self.progress.emit(f"Error: {e}")
            self.finished.emit(False)


class AuthScreen(QWidget):
    """
    Screen 3 - Authorization
    
    Runs OAuth flow and shows scope information.
    """
    
    auth_complete = Signal()
    back_clicked = Signal()
    
    def __init__(
        self,
        oauth_manager: OAuthManager,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        
        self.oauth_manager = oauth_manager
        self._auth_thread: Optional[QThread] = None
        self._auth_worker: Optional[AuthWorker] = None
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Header
        header = SectionHeader(
            "Authorization",
            "Grant read-only access to your Google Docs."
        )
        layout.addWidget(header)
        
        # Scopes card
        scopes_card = Card()
        
        scopes_title = QLabel("Permissions Requested")
        scopes_title.setStyleSheet("color: #1F2937; font-size: 16px; font-weight: bold;")
        scopes_card.layout.addWidget(scopes_title)
        
        scopes_info = QLabel(
            "This application will request the following read-only permissions:"
        )
        scopes_info.setStyleSheet("color: #6B7280; font-size: 14px;")
        scopes_info.setWordWrap(True)
        scopes_card.layout.addWidget(scopes_info)
        
        # Scope list
        for scope_desc in self.oauth_manager.get_scopes_display():
            scope_item = QLabel(f"  • {scope_desc}")
            scope_item.setStyleSheet("color: #1F2937; font-size: 14px;")
            scopes_card.layout.addWidget(scope_item)
        
        layout.addWidget(scopes_card)
        
        # Status card
        status_card = Card()
        
        status_title = QLabel("Authorization Status")
        status_title.setStyleSheet("color: #1F2937; font-size: 16px; font-weight: bold;")
        status_card.layout.addWidget(status_title)
        
        # Status indicator
        self.status = StatusIndicator()
        self.status.set_neutral("Ready to authorize")
        status_card.layout.addWidget(self.status)
        
        # Authorize button
        auth_button_layout = QHBoxLayout()
        
        self.auth_button = StyledButton("Authorize in Browser", primary=True)
        self.auth_button.clicked.connect(self._start_auth)
        auth_button_layout.addWidget(self.auth_button)
        
        auth_button_layout.addStretch()
        
        status_card.layout.addLayout(auth_button_layout)
        
        # Error panel
        self.error_panel = ErrorPanel()
        self.error_panel.retry_requested.connect(self._start_auth)
        status_card.layout.addWidget(self.error_panel)
        
        layout.addWidget(status_card)
        
        layout.addStretch()
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        
        back_button = StyledButton("Back", primary=False)
        back_button.clicked.connect(self.back_clicked.emit)
        nav_layout.addWidget(back_button)
        
        nav_layout.addStretch()
        
        self.continue_button = StyledButton("Continue", primary=True)
        self.continue_button.setEnabled(False)
        self.continue_button.clicked.connect(self.auth_complete.emit)
        nav_layout.addWidget(self.continue_button)
        
        layout.addLayout(nav_layout)
    
    def check_existing_auth(self) -> bool:
        """Check if already authenticated."""
        if self.oauth_manager.is_authenticated():
            self.status.set_success("Already authorized (read-only)")
            self.continue_button.setEnabled(True)
            return True
        return False
    
    def _start_auth(self) -> None:
        """Start the OAuth flow."""
        self.error_panel.clear()
        self.status.set_loading("Opening browser for authorization...")
        self.auth_button.setEnabled(False)
        
        # Run in thread to not block UI
        self._auth_thread = QThread()
        self._auth_worker = AuthWorker(self.oauth_manager)
        self._auth_worker.moveToThread(self._auth_thread)
        
        self._auth_thread.started.connect(self._auth_worker.run)
        self._auth_worker.progress.connect(self._on_auth_progress)
        self._auth_worker.finished.connect(self._on_auth_finished)
        self._auth_worker.finished.connect(self._auth_thread.quit)
        
        self._auth_thread.start()
    
    def _on_auth_progress(self, message: str) -> None:
        """Handle auth progress update."""
        self.status.set_loading(message)
    
    def _on_auth_finished(self, success: bool) -> None:
        """Handle auth completion."""
        self.auth_button.setEnabled(True)
        
        if success:
            self.status.set_success("Access granted (read-only)")
            self.continue_button.setEnabled(True)
        else:
            self.status.set_error("Authorization failed")
            self.error_panel.show_error(
                "Authorization Failed",
                "Could not complete the authorization flow.",
                "Make sure you completed the authorization in your browser and allowed access."
            )
