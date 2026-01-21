"""Document screen - document selection and validation."""

from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Signal, Qt, QThread, QObject

from gdhistogram.ui.widgets import (
    StyledButton, Card, StatusIndicator, 
    SectionHeader, ErrorPanel
)
from gdhistogram.api.google_client import GoogleClient, DocumentInfo


class ValidationWorker(QObject):
    """Worker for validating document in background thread."""
    
    finished = Signal(bool, str, object)  # success, message, doc_info
    
    def __init__(self, google_client: GoogleClient, input_str: str):
        super().__init__()
        self.google_client = google_client
        self.input_str = input_str
    
    def run(self) -> None:
        """Validate the document."""
        try:
            is_valid, message, doc_info = self.google_client.validate_document(
                self.input_str
            )
            self.finished.emit(is_valid, message, doc_info)
        except Exception as e:
            self.finished.emit(False, str(e), None)


class DocumentScreen(QWidget):
    """
    Screen 4 - Document Selection
    
    User pastes document URL or ID.
    """
    
    document_selected = Signal(object)  # Emits DocumentInfo
    back_clicked = Signal()
    
    def __init__(
        self,
        google_client: GoogleClient,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        
        self.google_client = google_client
        self._doc_info: Optional[DocumentInfo] = None
        self._validation_thread: Optional[QThread] = None
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Header
        header = SectionHeader(
            "Select Document",
            "Enter the Google Doc URL or file ID to analyze."
        )
        layout.addWidget(header)
        
        # Input card
        input_card = Card()
        
        input_title = QLabel("Document URL or ID")
        input_title.setStyleSheet("color: #1F2937; font-size: 16px; font-weight: bold;")
        input_card.layout.addWidget(input_title)
        
        # URL input
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText(
            "Paste Google Docs URL or file ID (e.g., https://docs.google.com/document/d/...)"
        )
        self.url_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #D1D5DB;
                border-radius: 6px;
                padding: 12px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #2563EB;
            }
        """)
        self.url_input.returnPressed.connect(self._validate_document)
        input_card.layout.addWidget(self.url_input)
        
        # Validate button row
        validate_row = QHBoxLayout()
        
        self.status = StatusIndicator()
        validate_row.addWidget(self.status)
        
        validate_row.addStretch()
        
        self.validate_button = StyledButton("Validate", primary=False)
        self.validate_button.clicked.connect(self._validate_document)
        validate_row.addWidget(self.validate_button)
        
        input_card.layout.addLayout(validate_row)
        
        # Error panel
        self.error_panel = ErrorPanel()
        self.error_panel.retry_requested.connect(self._validate_document)
        input_card.layout.addWidget(self.error_panel)
        
        layout.addWidget(input_card)
        
        # Document info card (hidden initially)
        self.doc_info_card = Card()
        self.doc_info_card.hide()
        
        doc_title_label = QLabel("Document Found")
        doc_title_label.setStyleSheet("color: #1F2937; font-size: 16px; font-weight: bold;")
        self.doc_info_card.layout.addWidget(doc_title_label)
        
        # Document details
        self.doc_title = QLabel()
        self.doc_title.setStyleSheet("color: #1F2937; font-size: 18px; font-weight: bold;")
        self.doc_info_card.layout.addWidget(self.doc_title)
        
        self.doc_owner = QLabel()
        self.doc_owner.setStyleSheet("color: #6B7280; font-size: 14px;")
        self.doc_info_card.layout.addWidget(self.doc_owner)
        
        self.doc_modified = QLabel()
        self.doc_modified.setStyleSheet("color: #6B7280; font-size: 14px;")
        self.doc_info_card.layout.addWidget(self.doc_modified)
        
        layout.addWidget(self.doc_info_card)
        
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
    
    def _validate_document(self) -> None:
        """Validate the entered document."""
        input_str = self.url_input.text().strip()
        
        if not input_str:
            self.error_panel.show_error(
                "No Input",
                "Please enter a Google Doc URL or file ID.",
                show_retry=False
            )
            return
        
        self.error_panel.clear()
        self.doc_info_card.hide()
        self.status.set_loading("Validating document...")
        self.validate_button.setEnabled(False)
        self.continue_button.setEnabled(False)
        
        # Run validation in thread
        self._validation_thread = QThread()
        self._validation_worker = ValidationWorker(self.google_client, input_str)
        self._validation_worker.moveToThread(self._validation_thread)
        
        self._validation_thread.started.connect(self._validation_worker.run)
        self._validation_worker.finished.connect(self._on_validation_finished)
        self._validation_worker.finished.connect(self._validation_thread.quit)
        
        self._validation_thread.start()
    
    def _on_validation_finished(
        self,
        success: bool,
        message: str,
        doc_info: Optional[DocumentInfo]
    ) -> None:
        """Handle validation result."""
        self.validate_button.setEnabled(True)
        
        if success and doc_info:
            self._doc_info = doc_info
            self.status.set_success("Document validated")
            
            # Show document info
            self.doc_title.setText(doc_info.title)
            self.doc_owner.setText(f"Owner: {doc_info.owner}")
            self.doc_modified.setText(f"Last modified: {doc_info.modified_time}")
            self.doc_info_card.show()
            
            self.continue_button.setEnabled(True)
        else:
            self._doc_info = None
            self.status.set_error("Validation failed")
            
            # Determine error type
            if "not found" in message.lower():
                action = "Check that the URL is correct and you have access to the document."
            elif "not a google doc" in message.lower():
                action = "This file is not a Google Doc. Only Google Docs are supported."
            elif "access denied" in message.lower():
                action = "You don't have permission to access this document."
            else:
                action = "Check the URL and try again."
            
            self.error_panel.show_error(
                "Document Validation Failed",
                message,
                action
            )
    
    def _on_continue(self) -> None:
        """Handle continue button click."""
        if self._doc_info:
            self.document_selected.emit(self._doc_info)
