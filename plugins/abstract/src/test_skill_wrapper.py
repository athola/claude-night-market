from wrapper_base import SuperpowerWrapper
import subprocess
import json

class TestSkillWrapper(SuperpowerWrapper):
    def __init__(self):
        super().__init__(
            source_plugin="abstract",
            source_command="test-skill",
            target_superpower="test-driven-development"
        )

    def execute(self, params: dict) -> dict:
        """Execute the wrapped test-skill command"""
        # Translate parameters
        superpower_params = self.translate_parameters(params)

        # Call superpower with skill-specific extensions
        result = {
            "superpower_called": self.target_superpower,
            "phase_executed": superpower_params.get("tdd_phase"),
            "target": superpower_params.get("target_under_test"),
            "extensions": self._apply_skill_extensions(superpower_params)
        }

        return result

    def _apply_skill_extensions(self, params: dict) -> dict:
        """Apply skill-specific extensions to superpower call"""
        extensions = {
            "skill_validation": True,
            "rationalization_detection": True,
            "skill_specific_reporting": True
        }

        # Add skill path to extensions for validation
        if "target_under_test" in params:
            extensions["skill_path"] = params["target_under_test"]

        return extensions