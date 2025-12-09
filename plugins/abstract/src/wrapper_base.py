from typing import Any


class SuperpowerWrapper:
    """Base class for wrapping plugin commands to superpower calls

    Provides parameter translation and common functionality for plugin
    command wrappers that delegate to superpower implementations.
    """

    def __init__(self, source_plugin: str, source_command: str, target_superpower: str):
        """Initialize the wrapper with plugin and command information

        Args:
            source_plugin: Name of the source plugin
            source_command: Name of the source command
            target_superpower: Name of the target superpower to call

        """
        self.source_plugin = source_plugin
        self.source_command = source_command
        self.target_superpower = target_superpower
        self.parameter_map = self._load_parameter_map()

    def translate_parameters(self, params: dict[str, Any]) -> dict[str, Any]:
        """Translate plugin parameters to superpower parameters

        Args:
            params: Dictionary of plugin parameters

        Returns:
            Dictionary of translated parameters for the superpower

        """
        translated = {}
        for key, value in params.items():
            mapped_key = self.parameter_map.get(key, key)
            translated[mapped_key] = value
        return translated

    def _load_parameter_map(self) -> dict[str, str]:
        """Load parameter mapping from wrapper config

        Returns:
            Dictionary mapping parameter names from plugin to superpower

        """
        # Default mapping for test-skill -> test-driven-development
        return {"skill-path": "target_under_test", "phase": "tdd_phase"}
