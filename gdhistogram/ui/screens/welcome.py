"""Welcome screen - initial state."""

from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

from gdhistogram.ui.widgets import StyledButton, Card


class WelcomeScreen(QWidget):
    """
    Screen 1 - Initial State
    
    Shows welcome message and start button.
    """
    
    start_clicked = Signal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Spacer at top
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Title
        title = QLabel("Document Revision Analysis")
        title_font = QFont()
        title_font.setPointSize(32)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #1F2937;")
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Analyze Google Docs revision history to understand typing patterns")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #6B7280; font-size: 16px;")
        layout.addWidget(subtitle)
        
        layout.addSpacing(40)
        
        # Feature cards
        features_layout = QHBoxLayout()
        features_layout.setSpacing(20)
        
        # Feature 1
        feature1 = self._create_feature_card(
            "🖥️",
            "Runs Locally",
            "All processing happens on your computer. No data sent to external servers."
        )
        features_layout.addWidget(feature1)
        
        # Feature 2
        feature2 = self._create_feature_card(
            "🔒",
            "Read-Only Access",
            "Only reads document revisions. Never modifies your documents."
        )
        features_layout.addWidget(feature2)
        
        # Feature 3
        feature3 = self._create_feature_card(
            "📊",
            "Deterministic Analysis",
            "Same document state always produces identical results."
        )
        features_layout.addWidget(feature3)
        
        layout.addLayout(features_layout)
        
        layout.addSpacing(40)
        
        # Start button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        start_button = StyledButton("Start Setup", primary=True)
        start_button.setMinimumWidth(200)
        start_button.clicked.connect(self.start_clicked.emit)
        button_layout.addWidget(start_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Spacer at bottom
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
    
    def _create_feature_card(
        self,
        icon: str,
        title: str,
        description: str
    ) -> Card:
        """Create a feature card."""
        card = Card()
        card.setFixedWidth(280)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 32px;")
        icon_label.setAlignment(Qt.AlignCenter)
        card.layout.addWidget(icon_label)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #1F2937; font-size: 16px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        card.layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setStyleSheet("color: #6B7280; font-size: 13px;")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        card.layout.addWidget(desc_label)
        
        return card
