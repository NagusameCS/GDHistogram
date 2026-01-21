"""Config screen - analysis configuration."""

from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox,
    QDoubleSpinBox, QGroupBox, QFormLayout, QFrame
)
from PySide6.QtCore import Signal, Qt

from gdhistogram.ui.widgets import StyledButton, Card, SectionHeader
from gdhistogram.config import AnalysisConfig, DEFAULT_CONFIG


class ConfigScreen(QWidget):
    """
    Screen 5 - Analysis Configuration
    
    Configure analysis parameters.
    """
    
    config_confirmed = Signal(object)  # Emits AnalysisConfig
    back_clicked = Signal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self._config = AnalysisConfig()
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Header
        header = SectionHeader(
            "Analysis Configuration",
            "Customize the analysis parameters. Default values work well for most documents."
        )
        layout.addWidget(header)
        
        # Basic settings card
        basic_card = Card()
        
        basic_title = QLabel("Basic Settings")
        basic_title.setStyleSheet("color: #1F2937; font-size: 16px; font-weight: bold;")
        basic_card.layout.addWidget(basic_title)
        
        basic_form = QFormLayout()
        basic_form.setSpacing(12)
        
        # Histogram bin size
        self.bin_size_spin = QSpinBox()
        self.bin_size_spin.setRange(1, 60)
        self.bin_size_spin.setValue(DEFAULT_CONFIG.bin_size_minutes)
        self.bin_size_spin.setSuffix(" minutes")
        self.bin_size_spin.setToolTip("Time interval for grouping WPM data in the histogram")
        basic_form.addRow("Histogram Bin Size:", self.bin_size_spin)
        
        # Max revisions
        self.max_revisions_spin = QSpinBox()
        self.max_revisions_spin.setRange(100, 10000)
        self.max_revisions_spin.setValue(DEFAULT_CONFIG.max_revisions)
        self.max_revisions_spin.setToolTip("Maximum number of revisions to process")
        basic_form.addRow("Max Revisions:", self.max_revisions_spin)
        
        basic_card.layout.addLayout(basic_form)
        layout.addWidget(basic_card)
        
        # Detection thresholds card
        detection_card = Card()
        
        detection_title = QLabel("Detection Thresholds")
        detection_title.setStyleSheet("color: #1F2937; font-size: 16px; font-weight: bold;")
        detection_card.layout.addWidget(detection_title)
        
        detection_form = QFormLayout()
        detection_form.setSpacing(12)
        
        # Copy/paste character threshold
        self.paste_chars_spin = QSpinBox()
        self.paste_chars_spin.setRange(10, 500)
        self.paste_chars_spin.setValue(DEFAULT_CONFIG.paste_chars_threshold)
        self.paste_chars_spin.setSuffix(" chars")
        self.paste_chars_spin.setToolTip("Minimum characters inserted to consider as potential paste")
        detection_form.addRow("Copy/Paste Char Threshold:", self.paste_chars_spin)
        
        # Copy/paste time threshold
        self.paste_time_spin = QDoubleSpinBox()
        self.paste_time_spin.setRange(1.0, 30.0)
        self.paste_time_spin.setValue(DEFAULT_CONFIG.paste_time_threshold_seconds)
        self.paste_time_spin.setSuffix(" seconds")
        self.paste_time_spin.setDecimals(1)
        self.paste_time_spin.setToolTip("Maximum time for insertion to be considered paste")
        detection_form.addRow("Copy/Paste Time Threshold:", self.paste_time_spin)
        
        # Spike Z-score threshold
        self.spike_z_spin = QDoubleSpinBox()
        self.spike_z_spin.setRange(1.0, 5.0)
        self.spike_z_spin.setValue(DEFAULT_CONFIG.spike_z_score_threshold)
        self.spike_z_spin.setDecimals(1)
        self.spike_z_spin.setToolTip("Standard deviations above mean WPM to flag as spike")
        detection_form.addRow("Spike Z-Score Threshold:", self.spike_z_spin)
        
        # Idle time threshold
        self.idle_time_spin = QDoubleSpinBox()
        self.idle_time_spin.setRange(1.0, 60.0)
        self.idle_time_spin.setValue(DEFAULT_CONFIG.idle_time_threshold_minutes)
        self.idle_time_spin.setSuffix(" minutes")
        self.idle_time_spin.setDecimals(1)
        self.idle_time_spin.setToolTip("Minimum idle time before activity is considered an idle burst")
        detection_form.addRow("Idle Time Threshold:", self.idle_time_spin)
        
        # Idle burst chars threshold
        self.idle_chars_spin = QSpinBox()
        self.idle_chars_spin.setRange(10, 500)
        self.idle_chars_spin.setValue(DEFAULT_CONFIG.idle_burst_chars_threshold)
        self.idle_chars_spin.setSuffix(" chars")
        self.idle_chars_spin.setToolTip("Minimum characters to consider as burst after idle")
        detection_form.addRow("Idle Burst Char Threshold:", self.idle_chars_spin)
        
        detection_card.layout.addLayout(detection_form)
        layout.addWidget(detection_card)
        
        # Reset button
        reset_layout = QHBoxLayout()
        reset_layout.addStretch()
        
        reset_button = StyledButton("Reset to Defaults", primary=False)
        reset_button.clicked.connect(self._reset_to_defaults)
        reset_layout.addWidget(reset_button)
        
        layout.addLayout(reset_layout)
        
        layout.addStretch()
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        
        back_button = StyledButton("Back", primary=False)
        back_button.clicked.connect(self.back_clicked.emit)
        nav_layout.addWidget(back_button)
        
        nav_layout.addStretch()
        
        run_button = StyledButton("Run Analysis", primary=True)
        run_button.clicked.connect(self._on_run)
        nav_layout.addWidget(run_button)
        
        layout.addLayout(nav_layout)
    
    def _reset_to_defaults(self) -> None:
        """Reset all values to defaults."""
        self.bin_size_spin.setValue(DEFAULT_CONFIG.bin_size_minutes)
        self.max_revisions_spin.setValue(DEFAULT_CONFIG.max_revisions)
        self.paste_chars_spin.setValue(DEFAULT_CONFIG.paste_chars_threshold)
        self.paste_time_spin.setValue(DEFAULT_CONFIG.paste_time_threshold_seconds)
        self.spike_z_spin.setValue(DEFAULT_CONFIG.spike_z_score_threshold)
        self.idle_time_spin.setValue(DEFAULT_CONFIG.idle_time_threshold_minutes)
        self.idle_chars_spin.setValue(DEFAULT_CONFIG.idle_burst_chars_threshold)
    
    def get_config(self) -> AnalysisConfig:
        """Get the current configuration."""
        return AnalysisConfig(
            bin_size_minutes=self.bin_size_spin.value(),
            max_revisions=self.max_revisions_spin.value(),
            paste_chars_threshold=self.paste_chars_spin.value(),
            paste_time_threshold_seconds=self.paste_time_spin.value(),
            spike_z_score_threshold=self.spike_z_spin.value(),
            idle_time_threshold_minutes=self.idle_time_spin.value(),
            idle_burst_chars_threshold=self.idle_chars_spin.value(),
        )
    
    def _on_run(self) -> None:
        """Handle run button click."""
        self.config_confirmed.emit(self.get_config())
