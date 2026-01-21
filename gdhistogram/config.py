"""Configuration constants for GDHistogram."""

from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# Application info
APP_NAME = "GDHistogram"
APP_VERSION = "1.0.0"

# Directory paths
APP_DATA_DIR = Path.home() / ".gdhistogram"
TOKENS_FILE = APP_DATA_DIR / "tokens.enc"
DATABASE_FILE = APP_DATA_DIR / "cache.db"
CONFIG_FILE = APP_DATA_DIR / "config.json"

# Google API scopes (read-only only!)
SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/documents.readonly",
]

# Google Doc MIME type
GOOGLE_DOC_MIME_TYPE = "application/vnd.google-apps.document"


@dataclass
class AnalysisConfig:
    """Configuration for analysis parameters."""
    
    # Histogram settings
    bin_size_minutes: int = 1
    
    # Copy/paste detection thresholds
    paste_chars_threshold: int = 50
    paste_time_threshold_seconds: float = 5.0
    paste_overlap_threshold: float = 0.3  # Low overlap with prior context
    
    # Spike detection
    spike_z_score_threshold: float = 3.0
    
    # Idle burst detection
    idle_time_threshold_minutes: float = 10.0
    idle_burst_chars_threshold: int = 100
    
    # Performance limits
    max_revisions: int = 2000
    
    # WPM calculation
    chars_per_word: int = 5
    max_valid_wpm: int = 500
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "bin_size_minutes": self.bin_size_minutes,
            "paste_chars_threshold": self.paste_chars_threshold,
            "paste_time_threshold_seconds": self.paste_time_threshold_seconds,
            "paste_overlap_threshold": self.paste_overlap_threshold,
            "spike_z_score_threshold": self.spike_z_score_threshold,
            "idle_time_threshold_minutes": self.idle_time_threshold_minutes,
            "idle_burst_chars_threshold": self.idle_burst_chars_threshold,
            "max_revisions": self.max_revisions,
            "chars_per_word": self.chars_per_word,
            "max_valid_wpm": self.max_valid_wpm,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "AnalysisConfig":
        """Create from dictionary."""
        return cls(
            bin_size_minutes=data.get("bin_size_minutes", 1),
            paste_chars_threshold=data.get("paste_chars_threshold", 50),
            paste_time_threshold_seconds=data.get("paste_time_threshold_seconds", 5.0),
            paste_overlap_threshold=data.get("paste_overlap_threshold", 0.3),
            spike_z_score_threshold=data.get("spike_z_score_threshold", 3.0),
            idle_time_threshold_minutes=data.get("idle_time_threshold_minutes", 10.0),
            idle_burst_chars_threshold=data.get("idle_burst_chars_threshold", 100),
            max_revisions=data.get("max_revisions", 2000),
            chars_per_word=data.get("chars_per_word", 5),
            max_valid_wpm=data.get("max_valid_wpm", 500),
        )


# Default configuration
DEFAULT_CONFIG = AnalysisConfig()

# UI Colors (colorblind-safe palette)
COLORS = {
    "primary": "#2563EB",      # Blue
    "success": "#059669",       # Green
    "warning": "#D97706",       # Orange
    "error": "#DC2626",         # Red
    "paste_event": "#DC2626",   # Red (copy/paste)
    "spike_event": "#D97706",   # Orange (spikes)
    "idle_event": "#2563EB",    # Blue (idle bursts)
    "background": "#FFFFFF",
    "surface": "#F3F4F6",
    "text": "#1F2937",
    "text_secondary": "#6B7280",
}

# Marker shapes (for accessibility - works without color)
MARKER_SHAPES = {
    "paste_event": "x",         # X for paste
    "spike_event": "triangle-up",  # Triangle for spike
    "idle_event": "diamond",    # Diamond for idle burst
}
