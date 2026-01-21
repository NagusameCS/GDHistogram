"""UI module for GDHistogram."""

# Lazy import to avoid loading PySide6 at module import time
def get_app():
    """Get the GDHistogramApp class."""
    from gdhistogram.ui.app import GDHistogramApp
    return GDHistogramApp

__all__ = ["get_app"]
