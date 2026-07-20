"""Pattern detection, coupling, and cohesion analysis (AR-01)."""

from __future__ import annotations

from typing import Any

from ._constants import (
    COHESION_SCORE_HIGH,
    COHESION_SCORE_MEDIUM,
    COUPLING_DEPENDENCY_SCALE,
    COUPLING_VIOLATION_WEIGHT,
    MIN_EVENT_COMPONENTS,
    MIN_LAYERS_FOR_LAYERED,
    MIN_RESPONSIBILITIES_FOR_LOW_COHESION,
    MIN_RESPONSIBILITIES_FOR_MEDIUM_COHESION,
    MIN_SERVICES_FOR_MICROSERVICES,
)


class PatternsMixin:
    """Pattern detection, coupling, and cohesion analysis."""

    @staticmethod
    def _detect_layered_pattern(files: list[str]) -> tuple[list[str], list[str]]:
        """Detect a layered architecture from controller/service/repo/model dirs."""
        layer_names = ["controllers", "services", "repositories", "models"]
        detected_layers = [
            layer for layer in layer_names if any(layer in f.lower() for f in files)
        ]
        if len(detected_layers) >= MIN_LAYERS_FOR_LAYERED:
            return ["layered"], detected_layers
        return [], []

    @staticmethod
    def _detect_hexagonal_pattern(
        files: list[str],
    ) -> tuple[list[str], dict[str, bool]]:
        """Detect a hexagonal (ports and adapters) architecture."""
        has_ports = any("ports" in f.lower() for f in files)
        has_adapters = any("adapters" in f.lower() for f in files)
        has_domain = any("domain" in f.lower() or "core" in f.lower() for f in files)

        if not (has_ports and has_adapters):
            return [], {}

        components = {"ports": True, "adapters": True}
        if has_domain:
            components["domain"] = True
        return ["hexagonal"], components

    @staticmethod
    def _detect_microservices_pattern(
        files: list[str],
    ) -> tuple[list[str], list[dict[str, str]]]:
        """Detect a microservices architecture from per-service directories."""
        service_dirs = set()
        for f in files:
            parts = f.split("/")
            for i, part in enumerate(parts):
                if part == "services" and i + 1 < len(parts):
                    service_dirs.add(parts[i + 1])
                elif "-service" in part or (part == "api-gateway" and i == 0):
                    service_dirs.add(part)

        if len(service_dirs) < MIN_SERVICES_FOR_MICROSERVICES:
            return [], []
        return ["microservices"], [{"name": name} for name in service_dirs]

    @staticmethod
    def _detect_event_driven_pattern(
        files: list[str],
    ) -> tuple[list[str], dict[str, bool]]:
        """Detect an event-driven architecture from handler/publisher dirs."""
        event_keywords = ["events", "handlers", "publishers", "subscribers"]
        detected = [
            keyword
            for keyword in event_keywords
            if any(keyword in f.lower() for f in files)
        ]
        if len(detected) < MIN_EVENT_COMPONENTS:
            return [], {}
        return ["event_driven"], dict.fromkeys(detected, True)

    def detect_architecture_pattern(self, context: Any) -> dict[str, Any]:
        """Detect architectural patterns in the codebase."""
        files = context.get_files()
        patterns = []
        layers = []
        components: dict[str, bool] = {}
        services: list[dict[str, str]] = []

        layered_patterns, detected_layers = self._detect_layered_pattern(files)
        patterns.extend(layered_patterns)
        layers.extend(detected_layers)

        hex_patterns, hex_components = self._detect_hexagonal_pattern(files)
        patterns.extend(hex_patterns)
        components.update(hex_components)

        micro_patterns, detected_services = self._detect_microservices_pattern(files)
        patterns.extend(micro_patterns)
        services.extend(detected_services)

        event_patterns, event_components = self._detect_event_driven_pattern(files)
        patterns.extend(event_patterns)
        components.update(event_components)

        return {
            "patterns": patterns,
            "layers": layers,
            "components": components,
            "services": services,
        }

    def analyze_coupling(self, context: Any) -> dict[str, Any]:
        """Analyze coupling between modules."""
        dependencies = context.analyze_dependencies()
        violations = []
        coupling_score = 0.0

        for dep in dependencies:
            from_module = dep.get("from", "")
            to_module = dep.get("to", "")

            if "controller" in from_module.lower() and "database" in to_module.lower():
                violations.append(
                    {
                        "type": "layering_violation",
                        "from": from_module,
                        "to": to_module,
                        "issue": "Controller accesses DB, bypassing service layer",
                    }
                )

            if (
                "controller" in from_module.lower()
                and "repository" in to_module.lower()
            ):
                violations.append(
                    {
                        "type": "layering_violation",
                        "from": from_module,
                        "to": to_module,
                        "issue": "Controller accesses repo, should use service layer",
                    }
                )

        if dependencies:
            coupling_score = len(dependencies) / COUPLING_DEPENDENCY_SCALE
            if violations:
                coupling_score += len(violations) * COUPLING_VIOLATION_WEIGHT

        return {
            "coupling_score": coupling_score,
            "violations": violations,
        }

    def analyze_cohesion(
        self,
        context: Any,
        module_path: str,
    ) -> dict[str, Any]:
        """Analyze cohesion within a module."""
        content = context.get_file_content(module_path)
        content_lower = content.lower()
        responsibilities = []
        cohesion_score = 1.0

        responsibility_keywords = {
            "user_management": [
                "create_user",
                "update_user",
                "delete_user",
                "get_user",
            ],
            "notification": ["send_notification", "send_email", "notify"],
            "billing": ["calculate_invoice", "process_payment", "charge"],
            "validation": ["validate_", "check_", "verify_"],
            "authentication": ["authenticate", "login", "logout"],
            "authorization": ["authorize", "has_permission", "check_role"],
        }

        for responsibility, keywords in responsibility_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                responsibilities.append(responsibility)

        if len(responsibilities) >= MIN_RESPONSIBILITIES_FOR_LOW_COHESION:
            cohesion_score = 1.0 / len(responsibilities)
        elif len(responsibilities) >= MIN_RESPONSIBILITIES_FOR_MEDIUM_COHESION:
            cohesion_score = COHESION_SCORE_MEDIUM
        else:
            cohesion_score = COHESION_SCORE_HIGH

        return {
            "cohesion_score": cohesion_score,
            "responsibilities": responsibilities,
        }


__all__ = ["PatternsMixin"]
