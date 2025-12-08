class SuperpowerWrapper:
    def __init__(self, source_plugin: str, source_command: str, target_superpower: str):
        self.source_plugin = source_plugin
        self.source_command = source_command
        self.target_superpower = target_superpower
        self.parameter_map = self._load_parameter_map()

    def translate_parameters(self, params: dict) -> dict:
        """Translate plugin parameters to superpower parameters"""
        translated = {}
        for key, value in params.items():
            mapped_key = self.parameter_map.get(key, key)
            translated[mapped_key] = value
        return translated

    def _load_parameter_map(self) -> dict:
        """Load parameter mapping from wrapper config"""
        # Default mapping for test-skill -> test-driven-development
        return {
            "skill-path": "target_under_test",
            "phase": "tdd_phase"
        }