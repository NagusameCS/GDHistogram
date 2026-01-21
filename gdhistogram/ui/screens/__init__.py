"""UI screens module for GDHistogram."""

from gdhistogram.ui.screens.welcome import WelcomeScreen
from gdhistogram.ui.screens.setup import SetupScreen
from gdhistogram.ui.screens.auth import AuthScreen
from gdhistogram.ui.screens.document import DocumentScreen
from gdhistogram.ui.screens.config import ConfigScreen
from gdhistogram.ui.screens.analysis import AnalysisScreen
from gdhistogram.ui.screens.results import ResultsScreen
from gdhistogram.ui.screens.export import ExportScreen

__all__ = [
    "WelcomeScreen",
    "SetupScreen",
    "AuthScreen",
    "DocumentScreen",
    "ConfigScreen",
    "AnalysisScreen",
    "ResultsScreen",
    "ExportScreen",
]
