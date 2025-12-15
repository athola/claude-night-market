"""Pensive exceptions module."""


class PensiveError(Exception):
    """Base exception for pensive."""


class ConfigurationError(PensiveError):
    """Configuration error."""


class AnalysisError(PensiveError):
    """Analysis error."""


class PluginError(PensiveError):
    """Plugin error."""


__all__ = [
    "AnalysisError",
    "ConfigurationError",
    "PensiveError",
    "PluginError",
]
