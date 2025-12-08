#!/usr/bin/env python3
"""Migration analyzer for detecting overlapping functionality between plugins and superpowers."""

import yaml
import os
from typing import Dict, List

class MigrationAnalyzer:
    def __init__(self, plugin_name: str):
        self.plugin_name = plugin_name
        # When running from within the plugin directory, use current directory
        self.plugin_path = os.path.abspath(".")
        self.overlap_mappings = self._load_overlap_mappings()

    def analyze_plugin(self, command_name: str) -> Dict:
        """Analyze a plugin command for superpower overlaps"""
        overlaps = {}

        # Load command content
        command_path = os.path.join(self.plugin_path, "commands", f"{command_name}.md")
        if os.path.exists(command_path):
            with open(command_path, 'r') as f:
                content = f.read()

            # Check for known patterns
            for superpower, patterns in self.overlap_mappings.items():
                confidence = self._calculate_overlap(content, patterns)
                if confidence > 0.5:
                    overlaps[superpower] = {
                        "confidence": confidence,
                        "patterns_matched": self._get_matched_patterns(content, patterns)
                    }

        return overlaps

    def _load_overlap_mappings(self) -> Dict:
        """Load predefined overlap patterns"""
        mappings_path = os.path.join(self.plugin_path, "data", "overlap_mappings.yaml")
        with open(mappings_path, 'r') as f:
            return yaml.safe_load(f)

    def _calculate_overlap(self, content: str, patterns: List[str]) -> float:
        """Calculate overlap confidence based on pattern matching"""
        matches = sum(1 for pattern in patterns if pattern.lower() in content.lower())
        return matches / len(patterns) if patterns else 0

    def _get_matched_patterns(self, content: str, patterns: List[str]) -> List[str]:
        """Get list of patterns that matched"""
        return [p for p in patterns if p.lower() in content.lower()]