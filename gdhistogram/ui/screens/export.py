"""Export screen - export options and audit."""

import json
import csv
import hashlib
from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PySide6.QtCore import Signal, Qt

from gdhistogram.ui.widgets import StyledButton, Card, SectionHeader, StatusIndicator
from gdhistogram.ui.screens.analysis import AnalysisResult
from gdhistogram.visualization.histogram import HistogramGenerator
from gdhistogram.config import SCOPES


class ExportScreen(QWidget):
    """
    Screen 8 - Export & Audit
    
    Export options and audit information.
    """
    
    back_clicked = Signal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self._result: Optional[AnalysisResult] = None
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Header
        header = SectionHeader(
            "Export & Audit",
            "Export analysis results and review audit information."
        )
        layout.addWidget(header)
        
        # Export options card
        export_card = Card()
        
        export_title = QLabel("Export Options")
        export_title.setStyleSheet("color: #1F2937; font-size: 16px; font-weight: bold;")
        export_card.layout.addWidget(export_title)
        
        # Export buttons row
        export_row = QHBoxLayout()
        
        # PNG export
        png_container = QWidget()
        png_layout = QVBoxLayout(png_container)
        png_layout.setContentsMargins(0, 0, 0, 0)
        
        png_button = StyledButton("Export PNG", primary=True)
        png_button.clicked.connect(self._export_png)
        png_layout.addWidget(png_button)
        
        png_label = QLabel("Histogram image")
        png_label.setStyleSheet("color: #6B7280; font-size: 12px;")
        png_label.setAlignment(Qt.AlignCenter)
        png_layout.addWidget(png_label)
        
        export_row.addWidget(png_container)
        
        # JSON export
        json_container = QWidget()
        json_layout = QVBoxLayout(json_container)
        json_layout.setContentsMargins(0, 0, 0, 0)
        
        json_button = StyledButton("Export JSON", primary=True)
        json_button.clicked.connect(self._export_json)
        json_layout.addWidget(json_button)
        
        json_label = QLabel("Raw metrics data")
        json_label.setStyleSheet("color: #6B7280; font-size: 12px;")
        json_label.setAlignment(Qt.AlignCenter)
        json_layout.addWidget(json_label)
        
        export_row.addWidget(json_container)
        
        # CSV export
        csv_container = QWidget()
        csv_layout = QVBoxLayout(csv_container)
        csv_layout.setContentsMargins(0, 0, 0, 0)
        
        csv_button = StyledButton("Export CSV", primary=True)
        csv_button.clicked.connect(self._export_csv)
        csv_layout.addWidget(csv_button)
        
        csv_label = QLabel("Event table")
        csv_label.setStyleSheet("color: #6B7280; font-size: 12px;")
        csv_label.setAlignment(Qt.AlignCenter)
        csv_layout.addWidget(csv_label)
        
        export_row.addWidget(csv_container)
        
        export_row.addStretch()
        
        export_card.layout.addLayout(export_row)
        
        # Status
        self.export_status = StatusIndicator()
        export_card.layout.addWidget(self.export_status)
        
        layout.addWidget(export_card)
        
        # Audit card
        audit_card = Card()
        
        audit_title = QLabel("Audit Information")
        audit_title.setStyleSheet("color: #1F2937; font-size: 16px; font-weight: bold;")
        audit_card.layout.addWidget(audit_title)
        
        # Audit table
        self.audit_table = QTableWidget()
        self.audit_table.setColumnCount(2)
        self.audit_table.setHorizontalHeaderLabels(["Property", "Value"])
        self.audit_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.audit_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.audit_table.verticalHeader().setVisible(False)
        self.audit_table.setAlternatingRowColors(True)
        self.audit_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.audit_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #E5E7EB;
                border-radius: 4px;
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
        audit_card.layout.addWidget(self.audit_table)
        
        layout.addWidget(audit_card)
        
        layout.addStretch()
        
        # Navigation
        nav_layout = QHBoxLayout()
        
        back_button = StyledButton("Back to Results", primary=False)
        back_button.clicked.connect(self.back_clicked.emit)
        nav_layout.addWidget(back_button)
        
        nav_layout.addStretch()
        
        layout.addLayout(nav_layout)
    
    def set_result(self, result: AnalysisResult) -> None:
        """Set the analysis result for export."""
        self._result = result
        self._populate_audit_table()
    
    def _populate_audit_table(self) -> None:
        """Populate the audit information table."""
        if not self._result:
            return
        
        result = self._result
        
        # Calculate revision hash
        revision_ids = sorted([r.id for r in result.revisions])
        revision_hash = hashlib.sha256(
            "|".join(revision_ids).encode()
        ).hexdigest()[:16]
        
        # Audit data
        audit_data = [
            ("Document ID", result.doc_info.file_id),
            ("Document Title", result.doc_info.title),
            ("APIs Used", "Google Drive API v3, Google Docs API v1"),
            ("Scopes Granted", ", ".join(SCOPES)),
            ("Total Revisions", str(len(result.revisions))),
            ("Analysis Config - Bin Size", f"{result.config.bin_size_minutes} minutes"),
            ("Analysis Config - Paste Threshold", f"{result.config.paste_chars_threshold} chars"),
            ("Analysis Config - Spike Z-Score", f"{result.config.spike_z_score_threshold}"),
            ("Revision Hash (integrity)", revision_hash),
        ]
        
        self.audit_table.setRowCount(len(audit_data))
        
        for i, (prop, value) in enumerate(audit_data):
            prop_item = QTableWidgetItem(prop)
            prop_item.setForeground(Qt.GlobalColor.darkGray)
            self.audit_table.setItem(i, 0, prop_item)
            
            value_item = QTableWidgetItem(value)
            self.audit_table.setItem(i, 1, value_item)
    
    def _export_png(self) -> None:
        """Export histogram as PNG."""
        if not self._result:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Histogram",
            f"{self._result.doc_info.title}_histogram.png",
            "PNG Files (*.png)"
        )
        
        if not file_path:
            return
        
        try:
            histogram_gen = HistogramGenerator(self._result.config)
            fig = histogram_gen.generate_histogram(
                self._result.metrics,
                self._result.events,
                self._result.statistics,
                title=f"WPM Analysis: {self._result.doc_info.title}"
            )
            histogram_gen.export_to_png(fig, file_path)
            
            self.export_status.set_success(f"Exported: {Path(file_path).name}")
        except Exception as e:
            self.export_status.set_error(f"Export failed: {e}")
            QMessageBox.warning(self, "Export Failed", str(e))
    
    def _export_json(self) -> None:
        """Export metrics as JSON."""
        if not self._result:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Metrics",
            f"{self._result.doc_info.title}_metrics.json",
            "JSON Files (*.json)"
        )
        
        if not file_path:
            return
        
        try:
            result = self._result
            
            export_data = {
                "document": {
                    "file_id": result.doc_info.file_id,
                    "title": result.doc_info.title,
                    "owner": result.doc_info.owner,
                },
                "config": result.config.to_dict(),
                "statistics": result.statistics.to_dict(),
                "metrics": [m.to_dict() for m in result.metrics],
                "events": [e.to_dict() for e in result.events],
                "revisions": [
                    {
                        "id": r.id,
                        "modified_time": r.modified_time.isoformat(),
                    }
                    for r in result.revisions
                ],
            }
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2)
            
            self.export_status.set_success(f"Exported: {Path(file_path).name}")
        except Exception as e:
            self.export_status.set_error(f"Export failed: {e}")
            QMessageBox.warning(self, "Export Failed", str(e))
    
    def _export_csv(self) -> None:
        """Export events as CSV."""
        if not self._result:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Events",
            f"{self._result.doc_info.title}_events.csv",
            "CSV Files (*.csv)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                
                # Header
                writer.writerow([
                    "Timestamp",
                    "Revision ID",
                    "Event Type",
                    "WPM",
                    "Chars Inserted",
                    "Time Delta (s)",
                    "Reason"
                ])
                
                # Data
                for event in self._result.events:
                    writer.writerow([
                        event.timestamp.isoformat(),
                        event.revision_id,
                        event.event_type.value,
                        f"{event.wpm:.2f}",
                        event.chars_inserted,
                        f"{event.time_delta_seconds:.2f}",
                        event.reason,
                    ])
            
            self.export_status.set_success(f"Exported: {Path(file_path).name}")
        except Exception as e:
            self.export_status.set_error(f"Export failed: {e}")
            QMessageBox.warning(self, "Export Failed", str(e))
