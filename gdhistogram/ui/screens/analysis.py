"""Analysis screen - analysis execution."""

from typing import Optional, List, Callable
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel
)
from PySide6.QtCore import Signal, Qt, QThread, QObject

from gdhistogram.ui.widgets import (
    StyledButton, Card, SectionHeader, ProgressPanel, ErrorPanel
)
from gdhistogram.api.google_client import GoogleClient, DocumentInfo
from gdhistogram.api.revision_fetcher import RevisionFetcher, RevisionMetadata
from gdhistogram.api.snapshot_exporter import SnapshotExporter, RevisionSnapshot
from gdhistogram.analysis.diff_engine import DiffEngine, DiffResult
from gdhistogram.analysis.metrics_engine import MetricsEngine, IntervalMetrics, OverallStatistics
from gdhistogram.analysis.event_detector import EventDetector, DetectedEvent
from gdhistogram.storage.database import Database, CacheManager
from gdhistogram.config import AnalysisConfig


class AnalysisResult:
    """Container for analysis results."""
    
    def __init__(
        self,
        doc_info: DocumentInfo,
        revisions: List[RevisionMetadata],
        snapshots: List[RevisionSnapshot],
        diffs: List[DiffResult],
        metrics: List[IntervalMetrics],
        statistics: OverallStatistics,
        events: List[DetectedEvent],
        config: AnalysisConfig
    ):
        self.doc_info = doc_info
        self.revisions = revisions
        self.snapshots = snapshots
        self.diffs = diffs
        self.metrics = metrics
        self.statistics = statistics
        self.events = events
        self.config = config


class AnalysisWorker(QObject):
    """Worker for running analysis in background thread."""
    
    progress = Signal(str, int, int)  # step, current, total
    finished = Signal(object)  # AnalysisResult or Exception
    
    def __init__(
        self,
        google_client: GoogleClient,
        doc_info: DocumentInfo,
        config: AnalysisConfig
    ):
        super().__init__()
        self.google_client = google_client
        self.doc_info = doc_info
        self.config = config
        self._cancelled = False
    
    def cancel(self) -> None:
        """Request cancellation."""
        self._cancelled = True
    
    def _check_cancelled(self) -> bool:
        """Check if cancelled."""
        return self._cancelled
    
    def run(self) -> None:
        """Run the analysis."""
        try:
            file_id = self.doc_info.file_id
            
            # Initialize components
            db = Database()
            cache_manager = CacheManager(db)
            revision_fetcher = RevisionFetcher(self.google_client)
            snapshot_exporter = SnapshotExporter(self.google_client)
            diff_engine = DiffEngine()
            metrics_engine = MetricsEngine(self.config)
            event_detector = EventDetector(self.config)
            
            # Step 1: Fetch revisions
            self.progress.emit("Fetching revisions...", 0, 0)
            
            if self._check_cancelled():
                raise Exception("Analysis cancelled")
            
            revisions = revision_fetcher.fetch_revisions(
                file_id,
                max_revisions=self.config.max_revisions,
                progress_callback=lambda c, t: self.progress.emit(
                    "Fetching revisions...", c, t if t > 0 else c
                )
            )
            
            if not revisions:
                raise Exception("No revisions found for this document")
            
            # Cache revisions
            db.save_revisions(file_id, revisions)
            
            # Step 2: Export snapshots
            self.progress.emit("Exporting snapshots...", 0, len(revisions))
            
            if self._check_cancelled():
                raise Exception("Analysis cancelled")
            
            # Check cache for existing snapshots
            cached_snapshots = db.get_all_cached_snapshots(file_id)
            snapshots: List[RevisionSnapshot] = []
            
            for i, rev in enumerate(revisions):
                if self._check_cancelled():
                    raise Exception("Analysis cancelled")
                
                if rev.id in cached_snapshots:
                    snapshots.append(cached_snapshots[rev.id])
                else:
                    snapshot = snapshot_exporter.export_revision(file_id, rev)
                    db.save_snapshot(file_id, snapshot)
                    snapshots.append(snapshot)
                
                self.progress.emit("Exporting snapshots...", i + 1, len(revisions))
            
            # Step 3: Compute diffs
            self.progress.emit("Computing diffs...", 0, len(snapshots) - 1)
            
            if self._check_cancelled():
                raise Exception("Analysis cancelled")
            
            diffs = diff_engine.compute_all_diffs(
                snapshots,
                progress_callback=lambda c, t: self.progress.emit(
                    "Computing diffs...", c, t
                )
            )
            
            # Step 4: Compute metrics
            self.progress.emit("Computing metrics...", 0, 1)
            
            if self._check_cancelled():
                raise Exception("Analysis cancelled")
            
            metrics = metrics_engine.compute_all_metrics(diffs)
            statistics = metrics_engine.compute_statistics(metrics, diffs)
            
            self.progress.emit("Computing metrics...", 1, 1)
            
            # Step 5: Detect events
            self.progress.emit("Detecting events...", 0, 1)
            
            if self._check_cancelled():
                raise Exception("Analysis cancelled")
            
            events = event_detector.detect_all_events(diffs, metrics, metrics_engine)
            
            self.progress.emit("Detecting events...", 1, 1)
            
            # Create result
            result = AnalysisResult(
                doc_info=self.doc_info,
                revisions=revisions,
                snapshots=snapshots,
                diffs=diffs,
                metrics=metrics,
                statistics=statistics,
                events=events,
                config=self.config
            )
            
            # Save analysis results
            db.save_document_info(
                file_id,
                self.doc_info.title,
                self.doc_info.owner,
                self.doc_info.created_time,
                self.doc_info.modified_time
            )
            
            db.save_analysis_results(
                file_id,
                self.config.to_dict(),
                {
                    "statistics": statistics.to_dict(),
                    "event_count": len(events),
                },
                [r.id for r in revisions]
            )
            
            self.finished.emit(result)
            
        except Exception as e:
            self.finished.emit(e)


class AnalysisScreen(QWidget):
    """
    Screen 6 - Analysis Execution
    
    Runs the analysis and shows progress.
    """
    
    analysis_complete = Signal(object)  # Emits AnalysisResult
    back_clicked = Signal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self._google_client: Optional[GoogleClient] = None
        self._doc_info: Optional[DocumentInfo] = None
        self._config: Optional[AnalysisConfig] = None
        self._analysis_thread: Optional[QThread] = None
        self._analysis_worker: Optional[AnalysisWorker] = None
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Header
        header = SectionHeader(
            "Running Analysis",
            "Processing document revisions. This may take a while for large documents."
        )
        layout.addWidget(header)
        
        # Document info
        self.doc_info_label = QLabel()
        self.doc_info_label.setStyleSheet("color: #6B7280; font-size: 14px;")
        layout.addWidget(self.doc_info_label)
        
        # Progress card
        progress_card = Card()
        
        self.progress_panel = ProgressPanel()
        self.progress_panel.cancel_requested.connect(self._on_cancel)
        progress_card.layout.addWidget(self.progress_panel)
        
        layout.addWidget(progress_card)
        
        # Error panel
        self.error_panel = ErrorPanel()
        self.error_panel.retry_requested.connect(self._start_analysis)
        layout.addWidget(self.error_panel)
        
        layout.addStretch()
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        
        self.back_button = StyledButton("Back", primary=False)
        self.back_button.clicked.connect(self._on_back)
        self.back_button.setEnabled(False)  # Disabled during analysis
        nav_layout.addWidget(self.back_button)
        
        nav_layout.addStretch()
        
        layout.addLayout(nav_layout)
    
    def start_analysis(
        self,
        google_client: GoogleClient,
        doc_info: DocumentInfo,
        config: AnalysisConfig
    ) -> None:
        """Start the analysis with given parameters."""
        self._google_client = google_client
        self._doc_info = doc_info
        self._config = config
        
        self.doc_info_label.setText(f"Analyzing: {doc_info.title}")
        
        self._start_analysis()
    
    def _start_analysis(self) -> None:
        """Start or restart the analysis."""
        if not all([self._google_client, self._doc_info, self._config]):
            return
        
        self.error_panel.clear()
        self.back_button.setEnabled(False)
        self.progress_panel.set_step("Initializing...")
        self.progress_panel.set_indeterminate()
        
        # Create worker and thread
        self._analysis_thread = QThread()
        self._analysis_worker = AnalysisWorker(
            self._google_client,
            self._doc_info,
            self._config
        )
        self._analysis_worker.moveToThread(self._analysis_thread)
        
        # Connect signals
        self._analysis_thread.started.connect(self._analysis_worker.run)
        self._analysis_worker.progress.connect(self._on_progress)
        self._analysis_worker.finished.connect(self._on_finished)
        self._analysis_worker.finished.connect(self._analysis_thread.quit)
        
        # Start
        self._analysis_thread.start()
    
    def _on_progress(self, step: str, current: int, total: int) -> None:
        """Handle progress update."""
        self.progress_panel.set_step(step)
        if total > 0:
            self.progress_panel.set_progress(current, total)
        else:
            self.progress_panel.set_indeterminate()
    
    def _on_finished(self, result) -> None:
        """Handle analysis completion."""
        self.back_button.setEnabled(True)
        
        if isinstance(result, Exception):
            error_msg = str(result)
            
            if "cancelled" in error_msg.lower():
                self.progress_panel.set_step("Cancelled")
                self.error_panel.show_error(
                    "Analysis Cancelled",
                    "The analysis was cancelled.",
                    show_retry=True
                )
            else:
                self.progress_panel.set_step("Failed")
                self.error_panel.show_error(
                    "Analysis Failed",
                    error_msg,
                    "Check your internet connection and try again.",
                    show_retry=True
                )
        else:
            self.progress_panel.set_complete()
            self.analysis_complete.emit(result)
    
    def _on_cancel(self) -> None:
        """Handle cancel request."""
        if self._analysis_worker:
            self._analysis_worker.cancel()
    
    def _on_back(self) -> None:
        """Handle back button."""
        # Clean up any running analysis
        if self._analysis_worker:
            self._analysis_worker.cancel()
        
        if self._analysis_thread and self._analysis_thread.isRunning():
            self._analysis_thread.quit()
            self._analysis_thread.wait(1000)
        
        self.back_clicked.emit()
