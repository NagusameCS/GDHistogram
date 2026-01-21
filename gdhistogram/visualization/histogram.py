"""Histogram generator using Plotly."""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from gdhistogram.analysis.metrics_engine import IntervalMetrics, OverallStatistics
from gdhistogram.analysis.event_detector import DetectedEvent, EventType
from gdhistogram.config import COLORS, MARKER_SHAPES, AnalysisConfig, DEFAULT_CONFIG


class HistogramGenerator:
    """
    Generator for WPM histograms using Plotly.
    
    Creates interactive, colorblind-safe visualizations with:
    - WPM over time
    - Event markers (paste, spike, idle burst)
    - Proper binning
    """
    
    def __init__(self, config: Optional[AnalysisConfig] = None):
        """
        Initialize the histogram generator.
        
        Args:
            config: Analysis configuration. Uses defaults if not provided.
        """
        self.config = config or DEFAULT_CONFIG
    
    def _bin_metrics_by_time(
        self,
        metrics: List[IntervalMetrics],
        bin_size_minutes: int
    ) -> Dict[datetime, List[IntervalMetrics]]:
        """
        Bin metrics by time intervals.
        
        Args:
            metrics: List of interval metrics.
            bin_size_minutes: Size of each bin in minutes.
        
        Returns:
            Dictionary mapping bin start time to metrics in that bin.
        """
        if not metrics:
            return {}
        
        bins: Dict[datetime, List[IntervalMetrics]] = defaultdict(list)
        bin_delta = timedelta(minutes=bin_size_minutes)
        
        # Find the start time (first metric)
        start_time = min(m.timestamp for m in metrics)
        
        # Normalize start time to bin boundary
        start_time = start_time.replace(second=0, microsecond=0)
        start_minute = start_time.minute - (start_time.minute % bin_size_minutes)
        start_time = start_time.replace(minute=start_minute)
        
        for m in metrics:
            # Calculate which bin this metric belongs to
            time_diff = m.timestamp - start_time
            bin_index = int(time_diff.total_seconds() / (bin_size_minutes * 60))
            bin_start = start_time + timedelta(minutes=bin_index * bin_size_minutes)
            bins[bin_start].append(m)
        
        return dict(bins)
    
    def _calculate_bin_wpm(
        self,
        bin_metrics: List[IntervalMetrics]
    ) -> float:
        """
        Calculate average WPM for a bin.
        
        Args:
            bin_metrics: Metrics in this bin.
        
        Returns:
            Average WPM (excluding anomalies).
        """
        valid_wpm = [m.wpm for m in bin_metrics if not m.is_anomaly]
        if not valid_wpm:
            return 0.0
        return sum(valid_wpm) / len(valid_wpm)
    
    def generate_histogram(
        self,
        metrics: List[IntervalMetrics],
        events: List[DetectedEvent],
        statistics: OverallStatistics,
        title: str = "Document Revision Analysis"
    ) -> go.Figure:
        """
        Generate an interactive histogram.
        
        Args:
            metrics: List of interval metrics.
            events: List of detected events.
            statistics: Overall statistics.
            title: Chart title.
        
        Returns:
            Plotly Figure object.
        """
        # Create figure with secondary y-axis for events
        fig = make_subplots(
            rows=2, cols=1,
            row_heights=[0.8, 0.2],
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=(title, "Events")
        )
        
        # Bin metrics
        bins = self._bin_metrics_by_time(metrics, self.config.bin_size_minutes)
        
        if bins:
            # Sort bins by time
            sorted_bins = sorted(bins.items())
            
            # Extract data for plotting
            times = [t for t, _ in sorted_bins]
            wpms = [self._calculate_bin_wpm(m) for _, m in sorted_bins]
            
            # Add WPM bars
            fig.add_trace(
                go.Bar(
                    x=times,
                    y=wpms,
                    name="WPM",
                    marker_color=COLORS["primary"],
                    hovertemplate=(
                        "<b>Time:</b> %{x}<br>"
                        "<b>WPM:</b> %{y:.1f}<br>"
                        "<extra></extra>"
                    ),
                ),
                row=1, col=1
            )
            
            # Add mean line
            fig.add_hline(
                y=statistics.mean_wpm,
                line_dash="dash",
                line_color=COLORS["text_secondary"],
                annotation_text=f"Mean: {statistics.mean_wpm:.1f} WPM",
                annotation_position="right",
                row=1, col=1
            )
        
        # Add event markers
        self._add_event_markers(fig, events)
        
        # Update layout
        fig.update_layout(
            height=600,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            plot_bgcolor=COLORS["background"],
            paper_bgcolor=COLORS["background"],
            font=dict(color=COLORS["text"]),
            hovermode="x unified",
        )
        
        # Update axes
        fig.update_xaxes(
            title_text="Time",
            gridcolor=COLORS["surface"],
            row=1, col=1
        )
        fig.update_yaxes(
            title_text="Words Per Minute (WPM)",
            gridcolor=COLORS["surface"],
            row=1, col=1
        )
        
        fig.update_xaxes(
            title_text="Time",
            gridcolor=COLORS["surface"],
            row=2, col=1
        )
        fig.update_yaxes(
            title_text="Event Type",
            gridcolor=COLORS["surface"],
            showticklabels=False,
            row=2, col=1
        )
        
        return fig
    
    def _add_event_markers(
        self,
        fig: go.Figure,
        events: List[DetectedEvent]
    ) -> None:
        """
        Add event markers to the figure.
        
        Args:
            fig: Plotly figure to modify.
            events: List of detected events.
        """
        # Group events by type
        paste_events = [e for e in events if e.event_type == EventType.COPY_PASTE]
        spike_events = [e for e in events if e.event_type == EventType.SPIKE]
        idle_events = [e for e in events if e.event_type == EventType.IDLE_BURST]
        
        # Add paste events (red X markers)
        if paste_events:
            fig.add_trace(
                go.Scatter(
                    x=[e.timestamp for e in paste_events],
                    y=[1 for _ in paste_events],
                    mode="markers",
                    name="Copy/Paste",
                    marker=dict(
                        color=COLORS["paste_event"],
                        size=12,
                        symbol=MARKER_SHAPES["paste_event"],
                        line=dict(width=2, color=COLORS["paste_event"])
                    ),
                    hovertemplate=(
                        "<b>Copy/Paste Event</b><br>"
                        "Time: %{x}<br>"
                        "%{customdata}<br>"
                        "<extra></extra>"
                    ),
                    customdata=[e.reason for e in paste_events],
                ),
                row=2, col=1
            )
        
        # Add spike events (orange triangle markers)
        if spike_events:
            fig.add_trace(
                go.Scatter(
                    x=[e.timestamp for e in spike_events],
                    y=[2 for _ in spike_events],
                    mode="markers",
                    name="Speed Spike",
                    marker=dict(
                        color=COLORS["spike_event"],
                        size=12,
                        symbol=MARKER_SHAPES["spike_event"],
                        line=dict(width=2, color=COLORS["spike_event"])
                    ),
                    hovertemplate=(
                        "<b>Speed Spike</b><br>"
                        "Time: %{x}<br>"
                        "%{customdata}<br>"
                        "<extra></extra>"
                    ),
                    customdata=[e.reason for e in spike_events],
                ),
                row=2, col=1
            )
        
        # Add idle burst events (blue diamond markers)
        if idle_events:
            fig.add_trace(
                go.Scatter(
                    x=[e.timestamp for e in idle_events],
                    y=[3 for _ in idle_events],
                    mode="markers",
                    name="Idle Burst",
                    marker=dict(
                        color=COLORS["idle_event"],
                        size=12,
                        symbol=MARKER_SHAPES["idle_event"],
                        line=dict(width=2, color=COLORS["idle_event"])
                    ),
                    hovertemplate=(
                        "<b>Idle Burst</b><br>"
                        "Time: %{x}<br>"
                        "%{customdata}<br>"
                        "<extra></extra>"
                    ),
                    customdata=[e.reason for e in idle_events],
                ),
                row=2, col=1
            )
    
    def export_to_png(
        self,
        fig: go.Figure,
        filepath: str,
        width: int = 1200,
        height: int = 800
    ) -> None:
        """
        Export histogram to PNG file.
        
        Args:
            fig: Plotly figure to export.
            filepath: Output file path.
            width: Image width in pixels.
            height: Image height in pixels.
        """
        fig.write_image(filepath, width=width, height=height, scale=2)
    
    def export_to_html(
        self,
        fig: go.Figure,
        filepath: str,
        include_plotlyjs: bool = True
    ) -> None:
        """
        Export histogram to interactive HTML file.
        
        Args:
            fig: Plotly figure to export.
            filepath: Output file path.
            include_plotlyjs: Whether to include Plotly.js in HTML.
        """
        fig.write_html(
            filepath,
            include_plotlyjs=include_plotlyjs,
            full_html=True
        )
    
    def get_figure_html(self, fig: go.Figure) -> str:
        """
        Get HTML representation of figure for embedding.
        
        Args:
            fig: Plotly figure.
        
        Returns:
            HTML string for embedding.
        """
        return fig.to_html(
            include_plotlyjs="cdn",
            full_html=False,
            div_id="histogram-container"
        )
