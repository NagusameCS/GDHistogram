"""Main application window for GDHistogram."""

import sys
from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import (
    QMainWindow, QApplication, QStackedWidget, QWidget,
    QVBoxLayout, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from gdhistogram.config import APP_NAME, APP_VERSION
from gdhistogram.auth.oauth_manager import OAuthManager
from gdhistogram.api.google_client import GoogleClient, DocumentInfo
from gdhistogram.ui.screens import (
    WelcomeScreen, SetupScreen, AuthScreen, DocumentScreen,
    ConfigScreen, AnalysisScreen, ResultsScreen, ExportScreen
)
from gdhistogram.ui.screens.analysis import AnalysisResult


class GDHistogramApp(QMainWindow):
    """
    Main application window.
    
    Manages the screen flow and application state.
    """
    
    # Screen indices
    SCREEN_WELCOME = 0
    SCREEN_SETUP = 1
    SCREEN_AUTH = 2
    SCREEN_DOCUMENT = 3
    SCREEN_CONFIG = 4
    SCREEN_ANALYSIS = 5
    SCREEN_RESULTS = 6
    SCREEN_EXPORT = 7
    
    def __init__(self):
        super().__init__()
        
        # State
        self._oauth_manager = OAuthManager()
        self._google_client: Optional[GoogleClient] = None
        self._doc_info: Optional[DocumentInfo] = None
        self._analysis_result: Optional[AnalysisResult] = None
        
        # Setup window
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(1024, 768)
        
        # Apply global styles
        self._apply_styles()
        
        # Create central widget with stacked layout
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Stacked widget for screens
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)
        
        # Create screens
        self._create_screens()
        
        # Start at welcome screen
        self._show_screen(self.SCREEN_WELCOME)
    
    def _apply_styles(self) -> None:
        """Apply global application styles."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F9FAFB;
            }
            QWidget {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            }
            QToolTip {
                background-color: #1F2937;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
            }
            QScrollBar:vertical {
                border: none;
                background-color: #F3F4F6;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #D1D5DB;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #9CA3AF;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)
    
    def _create_screens(self) -> None:
        """Create all application screens."""
        # Screen 1: Welcome
        self.welcome_screen = WelcomeScreen()
        self.welcome_screen.start_clicked.connect(self._on_start)
        self.stack.addWidget(self.welcome_screen)
        
        # Screen 2: Setup (OAuth credentials)
        self.setup_screen = SetupScreen()
        self.setup_screen.credentials_configured.connect(self._on_credentials_configured)
        self.setup_screen.back_clicked.connect(
            lambda: self._show_screen(self.SCREEN_WELCOME)
        )
        self.stack.addWidget(self.setup_screen)
        
        # Screen 3: Auth
        self.auth_screen = AuthScreen(self._oauth_manager)
        self.auth_screen.auth_complete.connect(self._on_auth_complete)
        self.auth_screen.back_clicked.connect(
            lambda: self._show_screen(self.SCREEN_SETUP)
        )
        self.stack.addWidget(self.auth_screen)
        
        # Screen 4: Document (placeholder - will be recreated with client)
        self.document_screen: Optional[DocumentScreen] = None
        self._document_placeholder = QWidget()
        self.stack.addWidget(self._document_placeholder)
        
        # Screen 5: Config
        self.config_screen = ConfigScreen()
        self.config_screen.config_confirmed.connect(self._on_config_confirmed)
        self.config_screen.back_clicked.connect(
            lambda: self._show_screen(self.SCREEN_DOCUMENT)
        )
        self.stack.addWidget(self.config_screen)
        
        # Screen 6: Analysis
        self.analysis_screen = AnalysisScreen()
        self.analysis_screen.analysis_complete.connect(self._on_analysis_complete)
        self.analysis_screen.back_clicked.connect(
            lambda: self._show_screen(self.SCREEN_CONFIG)
        )
        self.stack.addWidget(self.analysis_screen)
        
        # Screen 7: Results
        self.results_screen = ResultsScreen()
        self.results_screen.export_clicked.connect(self._on_export_clicked)
        self.results_screen.new_analysis_clicked.connect(self._on_new_analysis)
        self.stack.addWidget(self.results_screen)
        
        # Screen 8: Export
        self.export_screen = ExportScreen()
        self.export_screen.back_clicked.connect(
            lambda: self._show_screen(self.SCREEN_RESULTS)
        )
        self.stack.addWidget(self.export_screen)
    
    def _show_screen(self, index: int) -> None:
        """Show a specific screen."""
        self.stack.setCurrentIndex(index)
    
    def _on_start(self) -> None:
        """Handle start button click."""
        self._show_screen(self.SCREEN_SETUP)
    
    def _on_credentials_configured(self, file_path: str) -> None:
        """Handle credentials file selection."""
        try:
            self._oauth_manager.set_client_secrets(Path(file_path))
            
            # Check if already authenticated
            if self.auth_screen.check_existing_auth():
                # Skip auth screen if already authenticated
                self._on_auth_complete()
            else:
                self._show_screen(self.SCREEN_AUTH)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Configuration Error",
                f"Failed to configure credentials: {e}"
            )
    
    def _on_auth_complete(self) -> None:
        """Handle successful authentication."""
        # Create Google client with credentials
        creds = self._oauth_manager.get_credentials()
        if not creds:
            QMessageBox.critical(
                self,
                "Authentication Error",
                "Failed to get valid credentials."
            )
            return
        
        self._google_client = GoogleClient(creds)
        
        # Create/update document screen with client
        if self.document_screen:
            self.stack.removeWidget(self.document_screen)
            self.document_screen.deleteLater()
        
        self.document_screen = DocumentScreen(self._google_client)
        self.document_screen.document_selected.connect(self._on_document_selected)
        self.document_screen.back_clicked.connect(
            lambda: self._show_screen(self.SCREEN_AUTH)
        )
        
        # Replace placeholder
        self.stack.removeWidget(self._document_placeholder)
        self.stack.insertWidget(self.SCREEN_DOCUMENT, self.document_screen)
        
        self._show_screen(self.SCREEN_DOCUMENT)
    
    def _on_document_selected(self, doc_info: DocumentInfo) -> None:
        """Handle document selection."""
        self._doc_info = doc_info
        self._show_screen(self.SCREEN_CONFIG)
    
    def _on_config_confirmed(self, config) -> None:
        """Handle configuration confirmation."""
        if not self._google_client or not self._doc_info:
            return
        
        self._show_screen(self.SCREEN_ANALYSIS)
        self.analysis_screen.start_analysis(
            self._google_client,
            self._doc_info,
            config
        )
    
    def _on_analysis_complete(self, result: AnalysisResult) -> None:
        """Handle analysis completion."""
        self._analysis_result = result
        self.results_screen.set_result(result)
        self._show_screen(self.SCREEN_RESULTS)
    
    def _on_export_clicked(self, result: AnalysisResult) -> None:
        """Handle export button click."""
        self.export_screen.set_result(result)
        self._show_screen(self.SCREEN_EXPORT)
    
    def _on_new_analysis(self) -> None:
        """Handle new analysis request."""
        # Go back to document selection
        self._doc_info = None
        self._analysis_result = None
        self._show_screen(self.SCREEN_DOCUMENT)
    
    def closeEvent(self, event) -> None:
        """Handle window close."""
        # Confirm if analysis is running
        if (hasattr(self, 'analysis_screen') and 
            self.analysis_screen._analysis_thread and 
            self.analysis_screen._analysis_thread.isRunning()):
            
            reply = QMessageBox.question(
                self,
                "Confirm Exit",
                "Analysis is still running. Are you sure you want to exit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                event.ignore()
                return
            
            # Cancel and cleanup
            if self.analysis_screen._analysis_worker:
                self.analysis_screen._analysis_worker.cancel()
            
            self.analysis_screen._analysis_thread.quit()
            self.analysis_screen._analysis_thread.wait(2000)
        
        event.accept()


def run_app() -> int:
    """Run the application."""
    app = QApplication(sys.argv)
    
    # Set application info
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    
    # Create and show main window
    window = GDHistogramApp()
    window.show()
    
    return app.exec()
