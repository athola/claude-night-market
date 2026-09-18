#!/usr/bin/env python3
"""Architecture research module (REFACTORED with YAML matrix)."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

# Load decision matrix from YAML
DATA_DIR = Path(__file__).parent.parent / "data"
MATRIX_FILE = DATA_DIR / "paradigm_decision_matrix.yaml"


def load_decision_matrix() -> dict[str, Any]:
    """Load paradigm decision matrix from YAML file.

    Returns:
        Dictionary with matrix, modifiers, and project type preferences

    """
    if not MATRIX_FILE.exists():
        raise FileNotFoundError(
            f"Decision matrix not found: {MATRIX_FILE}\n"
            "Verify paradigm_decision_matrix.yaml exists"
        )

    with open(MATRIX_FILE) as f:
        result: dict[str, Any] = yaml.safe_load(f)
        return result


@dataclass
class ProjectContext:
    """Context about the project being initialized."""

    project_type: str
    domain_complexity: str
    team_size: str
    team_experience: str = "mixed"
    language: str = "python"
    scalability_needs: str = "moderate"
    security_requirements: str = "standard"


@dataclass
class ArchitectureRecommendation:
    """Recommended architecture with rationale."""

    paradigm: str
    primary: str
    secondary: str = ""
    rationale: str = ""
    confidence: str = "medium"
    trade_offs: dict[str, str] | None = None
    alternatives: list[dict[str, str]] | None = None


def parse_project_context(context_data: dict[str, str]) -> ProjectContext:
    """Parse context dictionary into ProjectContext object.

    Args:
        context_data: Dictionary with project context fields

    Returns:
        ProjectContext instance

    """
    return ProjectContext(
        project_type=context_data.get("project_type", "web-api"),
        domain_complexity=context_data.get("domain_complexity", "moderate"),
        team_size=context_data.get("team_size", "5-15"),
        team_experience=context_data.get("team_experience", "mixed"),
        language=context_data.get("language", "python"),
        scalability_needs=context_data.get("scalability_needs", "moderate"),
        security_requirements=context_data.get("security_requirements", "standard"),
    )


@dataclass
class ParadigmCandidate:
    """One paradigm with the score it earned and the rules that scored it."""

    paradigm: str
    score: float
    rules: list[str]


class ArchitectureResearcher:
    """Research and recommend architectures based on project context.

    Every paradigm the matrix cell or a modifier names is a candidate.
    ``rank`` scores them and ``recommend`` reports the top one with the
    runners-up attached. Confidence is the margin between first and
    second, so a tie reads ``low`` instead of a hard-coded ``high``.

    The modifier keys read here are the keys the data file uses.
    Until 2026-09 the code read ``preferred_paradigm``,
    ``fallback_paradigm`` and ``promote_patterns`` while the YAML said
    ``preferred``, ``avoid`` and ``recommended``, so no modifier had
    ever fired. ``tests/unit/test_architecture_researcher.py`` checks
    the two against each other.
    """

    CONSUMED_MODIFIER_KEYS = frozenset(
        {
            "preferred",
            "avoid",
            "recommended",
            "prefer_simple",
            "prefer_distributed",
            "additional_patterns",
            "require_isolation",
        }
    )
    HIGH_CONFIDENCE_MARGIN = 1.0

    # What the boolean modifiers refer to. The data says "prefer simple"
    # or "require isolation"; these name the paradigms that means.
    SIMPLE_PARADIGMS = ("layered", "functional-core")
    DISTRIBUTED_PARADIGMS = ("microservices", "event-driven", "cqrs-es")
    ISOLATING_PARADIGMS = ("hexagonal", "clean-architecture", "functional-core")

    _MATRIX_PRIMARY = 4.0
    _MATRIX_SECONDARY = 2.0
    _PREFERRED = 1.0
    _RECOMMENDED = 2.0
    _AVOID = -3.0
    _BOOLEAN = 1.0

    def __init__(self, context: ProjectContext) -> None:
        """Initialize architecture researcher."""
        self.context = context
        # Load decision matrix from YAML instead of embedding in code
        matrix_data = load_decision_matrix()
        self.PARADIGM_MATRIX = matrix_data["matrix"]
        self.project_type_modifiers = matrix_data.get("project_type_modifiers", {})
        self.scalability_modifiers = matrix_data.get("scalability_modifiers", {})
        self.security_modifiers = matrix_data.get("security_modifiers", {})

    def rank(
        self,
        context: ProjectContext | None = None,
        research: dict[str, Any] | None = None,
    ) -> list[ParadigmCandidate]:
        """Score every candidate paradigm for the context, best first.

        ``research`` is what the session found in Step 2 of
        architecture-aware-init, in the modifier vocabulary the data file
        uses: ``{"preferred": [...], "avoid": [...]}``. It is applied as a
        fourth modifier whose rules say "research", so a recommendation
        can show which points came from the matrix and which from what
        was read. Until 2026-09 the findings were accepted and dropped.

        Raises:
            ValueError: When the team size or complexity is not in the
                matrix. An unknown context is a caller bug, not a reason
                to guess.

        """
        context = context or self.context
        if context.team_size not in self.PARADIGM_MATRIX:
            raise ValueError(f"Unknown team size: {context.team_size}")
        team_matrix = self.PARADIGM_MATRIX[context.team_size]
        if context.domain_complexity not in team_matrix:
            raise ValueError(f"Unknown complexity: {context.domain_complexity}")
        cell = team_matrix[context.domain_complexity]

        scores: dict[str, float] = {}
        rules: dict[str, list[str]] = {}
        order: list[str] = []

        def add(paradigm: str, points: float, rule: str) -> None:
            if not paradigm:
                return
            if paradigm not in scores:
                scores[paradigm] = 0.0
                rules[paradigm] = []
                order.append(paradigm)
            scores[paradigm] += points
            rules[paradigm].append(rule)

        where = f"{context.team_size}/{context.domain_complexity}"
        add(cell["primary"], self._MATRIX_PRIMARY, f"matrix primary for {where}")
        add(
            cell.get("secondary", ""),
            self._MATRIX_SECONDARY,
            f"matrix secondary for {where}",
        )

        self._apply_modifier(
            add,
            self.project_type_modifiers.get(context.project_type, {}),
            f"project type {context.project_type}",
        )
        self._apply_modifier(
            add,
            self.scalability_modifiers.get(context.scalability_needs, {}),
            f"scalability {context.scalability_needs}",
        )
        self._apply_modifier(
            add,
            self.security_modifiers.get(context.security_requirements, {}),
            f"security {context.security_requirements}",
        )
        self._apply_modifier(add, research or {}, "research")

        position = {paradigm: index for index, paradigm in enumerate(order)}
        ranked = sorted(
            order, key=lambda paradigm: (-scores[paradigm], position[paradigm])
        )
        return [ParadigmCandidate(p, scores[p], rules[p]) for p in ranked]

    def _apply_modifier(self, add: Any, modifier: dict[str, Any], source: str) -> None:
        for paradigm in modifier.get("preferred", []):
            add(paradigm, self._PREFERRED, f"{source} prefers it")
        for paradigm in modifier.get("recommended", []) + modifier.get(
            "additional_patterns", []
        ):
            add(paradigm, self._RECOMMENDED, f"{source} recommends it")
        for paradigm in modifier.get("avoid", []):
            add(paradigm, self._AVOID, f"{source} avoids it")
        if modifier.get("prefer_simple"):
            for paradigm in self.SIMPLE_PARADIGMS:
                add(paradigm, self._BOOLEAN, f"{source} prefers simple")
        if modifier.get("prefer_distributed"):
            for paradigm in self.DISTRIBUTED_PARADIGMS:
                add(paradigm, self._BOOLEAN, f"{source} prefers distributed")
        if modifier.get("require_isolation"):
            for paradigm in self.ISOLATING_PARADIGMS:
                add(paradigm, self._BOOLEAN, f"{source} requires isolation")

    def recommend(
        self,
        context: ProjectContext | None = None,
        research: dict[str, Any] | None = None,
    ) -> ArchitectureRecommendation:
        """The top-ranked paradigm, with the runners-up and a margin-based confidence."""
        ranked = self.rank(context, research)
        top = ranked[0]
        runner_up = ranked[1] if len(ranked) > 1 else None
        margin = top.score - runner_up.score if runner_up else top.score
        confidence = "high" if margin >= self.HIGH_CONFIDENCE_MARGIN else "low"
        return ArchitectureRecommendation(
            paradigm=top.paradigm,
            primary=top.paradigm,
            secondary=runner_up.paradigm if runner_up else "",
            rationale="; ".join(top.rules),
            confidence=confidence,
            alternatives=[
                {
                    "paradigm": c.paradigm,
                    "score": str(c.score),
                    "rationale": "; ".join(c.rules),
                }
                for c in ranked[1:]
            ],
        )

    def generate_search_queries(self) -> list[str]:
        """Generate search queries for online research."""
        return [
            "architecture patterns best practices 2026",
            "software architecture decision framework",
        ]

    def recommend_paradigm(
        self, research_findings: dict[str, Any]
    ) -> ArchitectureRecommendation:
        """Recommend for the researcher's context with the session's research.

        ``research_findings`` carries ``preferred`` and ``avoid`` lists
        the session wrote after running the Step 2 queries; see
        ``load_research_file`` in ``attune_arch_init``.
        """
        return self.recommend(self.context, research_findings)

    def _build_recommendation(
        self,
        paradigm: str,
        secondary: str,
        rationale: str,
        _research_findings: dict[str, str],
    ) -> ArchitectureRecommendation:
        """Build recommendation with given parameters."""
        return ArchitectureRecommendation(
            paradigm=paradigm,
            primary=paradigm,
            secondary=secondary,
            rationale=rationale,
            confidence="high",
        )

    def save_research_session(self, output_path: Path) -> None:
        """Save research session to JSON file."""
        session_data = {
            "context": {
                "project_type": self.context.project_type,
                "domain_complexity": self.context.domain_complexity,
                "team_size": self.context.team_size,
                "language": self.context.language,
            },
            "queries": self.generate_search_queries(),
        }

        output_path.write_text(json.dumps(session_data, indent=2))


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Architecture researcher")
    parser.add_argument("--project-type", required=True)
    parser.add_argument("--team-size", required=True)
    parser.add_argument("--complexity", required=True)
    args = parser.parse_args()

    context = ProjectContext(
        project_type=args.project_type,
        team_size=args.team_size,
        domain_complexity=args.complexity,
    )

    researcher = ArchitectureResearcher(context)
    recommendation = researcher.recommend(context)
    print(f"Recommended: {recommendation.primary}")
    if recommendation.secondary:
        print(f"Alternative: {recommendation.secondary}")


if __name__ == "__main__":
    main()
