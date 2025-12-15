"""Language detection skill for parseltongue."""

from __future__ import annotations

from typing import Any


class LanguageDetectionSkill:
    """Skill for detecting programming languages in code."""

    def __init__(self) -> None:
        """Initialize the language detection skill."""
        pass

    async def detect_language(self, code: str, filename: str = "") -> dict[str, Any]:
        """Detect the programming language of the provided code.

        Args:
            code: Code to analyze
            filename: Optional filename hint

        Returns:
            Dictionary containing language detection results
        """
        # First, try to detect based on filename
        language_map = {
            ".py": ("python", 0.95),
            ".js": ("javascript", 0.95),
            ".jsx": ("javascript", 0.95),
            ".ts": ("typescript", 0.95),
            ".tsx": ("typescript", 0.95),
            ".rs": ("rust", 0.95),
        }

        for ext, (language, confidence) in language_map.items():
            if filename.endswith(ext):
                return {"language": language, "confidence": confidence}

        # If filename doesn't give a clear answer, use heuristics on code content
        if "def " in code or "import " in code:
            return {"language": "python", "confidence": 0.8}
        if "function " in code or "const " in code:
            return {"language": "javascript", "confidence": 0.8}

        # Default case
        return {"language": "unknown", "confidence": 0.5}
