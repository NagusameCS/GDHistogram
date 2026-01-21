"""Results screen - analysis results dashboard."""

from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QTabWidget, QScrollArea
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtWebEngineWidgets import QWebEngineView

from gdhistogram.ui.widgets import StyledButton, Card, SectionHeader
from gdhistogram.ui.screens.analysis import AnalysisResult
from gdhistogram.visualization.histogram import HistogramGenerator
from gdhistogram.analysis.event_detector import EventType


class ResultsScreen(QWidget):
    """
    Screen 7 - Results Dashboard
    
    Shows histogram and event table.
    """
    
    export_clicked = Signal(object)  # Emits AnalysisResult
    new_analysis_clicked = Signal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self._result: Optional[AnalysisResult] = None
        self._histogram_html: Optional[str] = None
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Header row
        header_row = QHBoxLayout()
        
        self.title_label = QLabel("Analysis Results")
        self.title_label.setStyleSheet("color: #1F2937; font-size: 24px; font-weight: bold;")
        header_row.addWidget(self.title_label)
        
        header_row.addStretch()
        
        new_button = StyledButton("New Analysis", primary=False)
        new_button.clicked.connect(self.new_analysis_clicked.emit)
        header_row.addWidget(new_button)
        
        export_button = StyledButton("Export", primary=True)
        export_button.clicked.connect(self._on_export)
        header_row.addWidget(export_button)
        
        layout.addLayout(header_row)
        
        # Tab widget
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                background-color: white;
            }
            QTabBar::tab {
                padding: 8px 16px;
                margin-right: 4px;
                border: 1px solid #E5E7EB;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                background-color: #F3F4F6;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 1px solid white;
            }
        """)
        
        # Histogram tab
        histogram_tab = QWidget()
        histogram_layout = QVBoxLayout(histogram_tab)
        histogram_layout.setContentsMargins(0, 0, 0, 0)
        
        self.histogram_view = QWebEngineView()
        self.histogram_view.setMinimumHeight(500)
        histogram_layout.addWidget(self.histogram_view)
        
        tabs.addTab(histogram_tab, "Histogram")
        
        # Events tab
        events_tab = QWidget()
        events_layout = QVBoxLayout(events_tab)
        events_layout.setContentsMargins(16, 16, 16, 16)
        
        self.events_table = QTableWidget()
        self.events_table.setColumnCount(5)
        self.events_table.setHorizontalHeaderLabels([
            "Time", "Event Type", "WPM", "Chars", "Details"
        ])
        self.events_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.events_table.setAlternatingRowColors(True)
        self.events_table.setStyleSheet("""
            QTableWidget {
                border: none;
                gridline-color: #E5E7EB;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #F3F4F6;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #E5E7EB;
                font-weight: bold;
            }
        """)
        events_layout.addWidget(self.events_table)
        
        tabs.addTab(events_tab, "Events")
        
        # Statistics tab
        stats_tab = QWidget()
        stats_layout = QVBoxLayout(stats_tab)
        stats_layout.setContentsMargins(16, 16, 16, 16)
        
        # Create scroll area for stats
        stats_scroll = QScrollArea()
        stats_scroll.setWidgetResizable(True)
        stats_scroll.setFrameShape(QScrollArea.NoFrame)
        
        stats_content = QWidget()
        self.stats_layout = QVBoxLayout(stats_content)
        self.stats_layout.setSpacing(16)
        stats_scroll.setWidget(stats_content)
        
        stats_layout.addWidget(stats_scroll)
        
        tabs.addTab(stats_tab, "Statistics")
        
        layout.addWidget(tabs)
    
    def set_result(self, result: AnalysisResult) -> None:
        """Set and display the analysis result."""
        self._result = result
        
        # Update title
        self.title_label.setText(f"Results: {result.doc_info.title}")
        
        # Generate and display histogram
        histogram_gen = HistogramGenerator(result.config)
        fig = histogram_gen.generate_histogram(
            result.metrics,
            result.events,
            result.statistics,
            title=f"WPM Analysis: {result.doc_info.title}"
        )
        
        self._histogram_html = histogram_gen.get_figure_html(fig)
        self.histogram_view.setHtml(self._histogram_html)
        
        # Populate events table
        self._populate_events_table(result.events)
        
        # Populate statistics
        self._populate_statistics(result)
    
    def _populate_events_table(self, events) -> None:
        """Populate the events table."""
        self.events_table.setRowCount(len(events))
        
        event_colors = {
            EventType.COPY_PASTE: "#FEE2E2",  # Light red
            EventType.SPIKE: "#FEF3C7",       # Light orange
            EventType.IDLE_BURST: "#DBEAFE",  # Light blue
        }
        
        for i, event in enumerate(events):
            # Time
            time_item = QTableWidgetItem(
                event.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            )
            self.events_table.setItem(i, 0, time_item)
            
            # Event type
            type_item = QTableWidgetItem(event.display_name)
            type_item.setBackground(
                Qt.GlobalColor.white  # Will be set by stylesheet
            )
            self.events_table.setItem(i, 1, type_item)
            
            # WPM
            wpm_item = QTableWidgetItem(f"{event.wpm:.1f}")
            self.events_table.setItem(i, 2, wpm_item)
            
            # Chars
            chars_item = QTableWidgetItem(str(event.chars_inserted))
            self.events_table.setItem(i, 3, chars_item)
            
            # Details
            details_item = QTableWidgetItem(event.reason)
            self.events_table.setItem(i, 4, details_item)
    
    def _populate_statistics(self, result: AnalysisResult) -> None:
        """Populate the statistics panel."""
        # Clear existing
        while self.stats_layout.count():
            child = self.stats_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        stats = result.statistics
        
        # Summary card
        summary_card = Card()
        
        summary_title = QLabel("Summary")
        summary_title.setStyleSheet("color: #1F2937; font-size: 16px; font-weight: bold;")
        summary_card.layout.addWidget(summary_title)
        
        summary_grid = QHBoxLayout()
        
        self._add_stat_item(summary_grid, "Total Revisions", str(stats.total_intervals + 1))
        self._add_stat_item(summary_grid, "Valid Intervals", str(stats.valid_intervals))
        self._add_stat_item(summary_grid, "Total Events", str(len(result.events)))
        
        summary_card.layout.addLayout(summary_grid)
        self.stats_layout.addWidget(summary_card)
        
        # WPM Statistics card
        wpm_card = Card()
        
        wpm_title = QLabel("Words Per Minute Statistics")
        wpm_title.setStyleSheet("color: #1F2937; font-size: 16px; font-weight: bold;")
        wpm_card.layout.addWidget(wpm_title)
        
        wpm_grid = QHBoxLayout()
        
        self._add_stat_item(wpm_grid, "Mean WPM", f"{stats.mean_wpm:.1f}")
        self._add_stat_item(wpm_grid, "Median WPM", f"{stats.median_wpm:.1f}")
        self._add_stat_item(wpm_grid, "Max WPM", f"{stats.max_wpm:.1f}")
        self._add_stat_item(wpm_grid, "Std Dev", f"{stats.std_wpm:.1f}")
        
        wpm_card.layout.addLayout(wpm_grid)
        self.stats_layout.addWidget(wpm_card)
        
        # Character Statistics card
        char_card = Card()
        
        char_title = QLabel("Character Statistics")
        char_title.setStyleSheet("color: #1F2937; font-size: 16px; font-weight: bold;")
        char_card.layout.addWidget(char_title)
        
        char_grid = QHBoxLayout()
        
        self._add_stat_item(char_grid, "Total Inserted", f"{stats.total_chars_inserted:,}")
        self._add_stat_item(char_grid, "Total Deleted", f"{stats.total_chars_deleted:,}")
        self._add_stat_item(char_grid, "Net Change", f"{stats.total_net_chars:,}")
        
        char_card.layout.addLayout(char_grid)
        self.stats_layout.addWidget(char_card)
        
        # Event breakdown card
        event_card = Card()
        
        event_title = QLabel("Event Breakdown")
        event_title.setStyleSheet("color: #1F2937; font-size: 16px; font-weight: bold;")
        event_card.layout.addWidget(event_title)
        
        event_grid = QHBoxLayout()
        
        paste_count = sum(1 for e in result.events if e.event_type == EventType.COPY_PASTE)
        spike_count = sum(1 for e in result.events if e.event_type == EventType.SPIKE)
        idle_count = sum(1 for e in result.events if e.event_type == EventType.IDLE_BURST)
        
        self._add_stat_item(event_grid, "Copy/Paste", str(paste_count), "#DC2626")
        self._add_stat_item(event_grid, "Speed Spikes", str(spike_count), "#D97706")
        self._add_stat_item(event_grid, "Idle Bursts", str(idle_count), "#2563EB")
        
        event_card.layout.addLayout(event_grid)
        self.stats_layout.addWidget(event_card)
        
        # Time range card
        time_card = Card()
        
        time_title = QLabel("Time Range")
        time_title.setStyleSheet("color: #1F2937; font-size: 16px; font-weight: bold;")
        time_card.layout.addWidget(time_title)
        
        if stats.first_revision_time and stats.last_revision_time:
            first_time = stats.first_revision_time.strftime("%Y-%m-%d %H:%M")
            last_time = stats.last_revision_time.strftime("%Y-%m-%d %H:%M")
            duration_hours = stats.total_time_seconds / 3600
            
            time_grid = QHBoxLayout()
            self._add_stat_item(time_grid, "First Revision", first_time)
            self._add_stat_item(time_grid, "Last Revision", last_time)
            self._add_stat_item(time_grid, "Total Duration", f"{duration_hours:.1f} hours")
            time_card.layout.addLayout(time_grid)
        
        self.stats_layout.addWidget(time_card)
        
        self.stats_layout.addStretch()
    
    def _add_stat_item(
        self,
        layout: QHBoxLayout,
        label: str,
        value: str,
        color: str = "#2563EB"
    ) -> None:
        """Add a stat item to a layout."""
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(8, 8, 8, 8)
        container_layout.setSpacing(4)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: bold;")
        value_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(value_label)
        
        name_label = QLabel(label)
        name_label.setStyleSheet("color: #6B7280; font-size: 12px;")
        name_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(name_label)
        
        layout.addWidget(container)
    
    def _on_export(self) -> None:
        """Handle export button click."""
        if self._result:
            self.export_clicked.emit(self._result)
