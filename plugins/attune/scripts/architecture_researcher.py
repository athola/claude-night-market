#!/usr/bin/env python3
"""Architecture research module combining online research with archetype matching."""

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ProjectContext:
    """Context about the project being initialized."""

    project_type: str  # "web-api", "cli-tool", "data-pipeline", "library", etc.
    domain_complexity: str  # "simple", "moderate", "complex", "highly-complex"
    team_size: str  # "<5", "5-15", "15-50", "50+"
    team_experience: str  # "junior", "mixed", "senior", "expert"
    team_distribution: str  # "co-located", "remote", "distributed"
    language: str  # "python", "rust", "typescript"
    framework: str = ""  # Optional: specific framework
    scalability_needs: str = "moderate"  # "low", "moderate", "high", "extreme"
    security_requirements: str = "standard"  # "standard", "high", "critical"
    integration_points: list[str] = field(default_factory=list)
    time_to_market: str = "normal"  # "rapid", "normal", "not-urgent"
    constraints: list[str] = field(default_factory=list)


@dataclass
class ArchitectureRecommendation:
    """Recommended architecture with rationale."""

    paradigm: str
    primary: str
    secondary: str = ""
    rationale: str = ""
    research_findings: dict[str, str] = field(default_factory=dict)
    trade_offs: dict[str, str] = field(default_factory=dict)
    alternatives: list[dict[str, str]] = field(default_factory=list)
    confidence: str = "medium"  # "low", "medium", "high"


class ArchitectureResearcher:
    """Research and recommend architectures based on project context."""

    # Paradigm decision matrix
    PARADIGM_MATRIX: dict[str, dict[str, dict[str, str]]] = {
        "<5": {
            "simple": {"primary": "layered", "secondary": ""},
            "moderate": {"primary": "layered", "secondary": "hexagonal"},
            "complex": {"primary": "hexagonal", "secondary": "functional-core"},
            "highly-complex": {
                "primary": "functional-core",
                "secondary": "hexagonal",
            },
        },
        "5-15": {
            "simple": {"primary": "layered", "secondary": ""},
            "moderate": {"primary": "modular-monolith", "secondary": "hexagonal"},
            "complex": {
                "primary": "modular-monolith",
                "secondary": "functional-core",
            },
            "highly-complex": {
                "primary": "hexagonal",
                "secondary": "functional-core",
            },
        },
        "15-50": {
            "simple": {"primary": "modular-monolith", "secondary": ""},
            "moderate": {"primary": "microservices", "secondary": "modular-monolith"},
            "complex": {"primary": "microservices", "secondary": "event-driven"},
            "highly-complex": {"primary": "cqrs-es", "secondary": "event-driven"},
        },
        "50+": {
            "simple": {"primary": "microservices", "secondary": ""},
            "moderate": {
                "primary": "microservices",
                "secondary": "event-driven",
            },
            "complex": {"primary": "event-driven", "secondary": "cqrs-es"},
            "highly-complex": {"primary": "microkernel", "secondary": "space-based"},
        },
    }

    # Special case overrides
    SPECIAL_CASES: dict[str, dict[str, str]] = {
        "real-time": {"primary": "event-driven", "secondary": "pipeline"},
        "streaming": {"primary": "event-driven", "secondary": "pipeline"},
        "bursty": {"primary": "serverless", "secondary": "microservices"},
        "cloud-native": {"primary": "serverless", "secondary": "microservices"},
        "extensible": {"primary": "microkernel", "secondary": "hexagonal"},
        "data-processing": {"primary": "pipeline", "secondary": "event-driven"},
        "legacy-integration": {"primary": "hexagonal", "secondary": "modular-monolith"},
        "high-throughput-stateful": {
            "primary": "space-based",
            "secondary": "event-driven",
        },
    }

    def __init__(self, context: ProjectContext):
        """Initialize researcher with project context.

        Args:
            context: Project context information

        """
        self.context = context
        self.research_results: dict[str, Any] = {}

    def generate_search_queries(self) -> list[str]:
        """Generate search queries for online research.

        Returns:
            List of search query strings

        """
        queries = []

        # Primary: Architecture patterns for project type
        queries.append(f"{self.context.project_type} architecture best practices 2026")

        # Secondary: Language-specific patterns
        lang = self.context.language
        proj = self.context.project_type
        queries.append(f"{lang} {proj} architecture patterns 2026")

        # Tertiary: Framework-specific if provided
        if self.context.framework:
            fw = self.context.framework
            queries.append(f"{fw} architecture patterns {proj}")

        # Quaternary: Domain complexity specific
        if self.context.domain_complexity in ["complex", "highly-complex"]:
            complexity = self.context.domain_complexity
            queries.append(f"{complexity} domain architecture patterns {lang}")

        # Special requirements
        if self.context.security_requirements == "critical":
            queries.append(f"secure architecture patterns {self.context.project_type}")

        if self.context.scalability_needs in ["high", "extreme"]:
            queries.append(
                f"scalable architecture patterns {self.context.project_type}"
            )

        return queries

    def recommend_paradigm(
        self, research_data: dict[str, str] | None = None
    ) -> ArchitectureRecommendation:
        """Recommend architecture paradigm based on context and research.

        Args:
            research_data: Optional research findings from online sources

        Returns:
            Architecture recommendation with rationale

        """
        # Check special cases first
        for keyword, paradigm in self.SPECIAL_CASES.items():
            if keyword in self.context.project_type.lower():
                return self._build_recommendation(
                    paradigm["primary"],
                    paradigm.get("secondary", ""),
                    "special-case",
                    research_data,
                )

        # Use decision matrix
        team_size = self.context.team_size
        complexity = self.context.domain_complexity

        if (
            team_size in self.PARADIGM_MATRIX
            and complexity in self.PARADIGM_MATRIX[team_size]
        ):
            matrix_result = self.PARADIGM_MATRIX[team_size][complexity]
            return self._build_recommendation(
                matrix_result["primary"],
                matrix_result.get("secondary", ""),
                "matrix",
                research_data,
            )

        # Fallback
        return self._build_recommendation("layered", "", "fallback", research_data)

    def _build_recommendation(
        self,
        primary: str,
        secondary: str,
        method: str,
        research_data: dict[str, str] | None,
    ) -> ArchitectureRecommendation:
        """Build architecture recommendation with rationale.

        Args:
            primary: Primary paradigm
            secondary: Secondary paradigm (if any)
            method: Selection method used
            research_data: Research findings

        Returns:
            Complete architecture recommendation

        """
        rationale_parts = [
            f"**Selected Based On**: {method} selection",
            f"**Team Size**: {self.context.team_size}",
            f"**Domain Complexity**: {self.context.domain_complexity}",
            f"**Project Type**: {self.context.project_type}",
        ]

        # Add research-based rationale if available
        if research_data:
            rationale_parts.append("\n**Research Findings**:")
            for key, value in research_data.items():
                rationale_parts.append(f"- {key}: {value}")

        return ArchitectureRecommendation(
            paradigm=primary,
            primary=primary,
            secondary=secondary,
            rationale="\n".join(rationale_parts),
            research_findings=research_data or {},
            trade_offs=self._identify_trade_offs(primary),
            alternatives=self._generate_alternatives(primary),
            confidence="high" if method in ["special-case", "matrix"] else "medium",
        )

    def _identify_trade_offs(self, paradigm: str) -> dict[str, str]:
        """Identify trade-offs for the selected paradigm.

        Args:
            paradigm: Selected paradigm name

        Returns:
            Dictionary of trade-offs and mitigations

        """
        trade_offs = {
            "layered": {
                "trade-off": "Anemic domain models, tight layer coupling",
                "mitigation": "Business logic in service layer, DTOs at boundaries",
                "best-for": "Teams new to architecture, CRUD-heavy apps",
                "avoid-when": "Complex domain or frequent infrastructure changes",
            },
            "hexagonal": {
                "trade-off": "More boilerplate, indirection through ports/adapters",
                "mitigation": "Code generation for adapters, minimal stable ports",
                "best-for": "Infrastructure flexibility, testability priority",
                "avoid-when": "Simple CRUD applications or very small teams",
            },
            "functional-core": {
                "trade-off": "Learning curve for functional thinking, discipline",
                "mitigation": "Start small, pair program, document patterns",
                "best-for": "Complex business logic, high testability needs",
                "avoid-when": "Team unfamiliar with functional programming",
            },
            "modular-monolith": {
                "trade-off": "Single deployment unit, module coupling risks",
                "mitigation": "Enforce boundaries via build tools, plan extraction",
                "best-for": "Growing teams, unclear service boundaries",
                "avoid-when": "Clear bounded contexts, microservices experience",
            },
            "microservices": {
                "trade-off": "Distributed complexity, latency, data consistency",
                "mitigation": "Invest in observability, automation, service mesh",
                "best-for": "Large teams, independent scaling, clear boundaries",
                "avoid-when": "Small teams, unclear boundaries, limited DevOps",
            },
            "cqrs-es": {
                "trade-off": "Complexity, eventual consistency, event versioning",
                "mitigation": "Start with single bounded context, event upcasting",
                "best-for": "Audit requirements, complex domain, temporal queries",
                "avoid-when": "Simple CRUD, unfamiliar with event-driven patterns",
            },
            "event-driven": {
                "trade-off": "Debugging complexity, eventual consistency, ordering",
                "mitigation": "Correlation IDs, distributed tracing, idempotency",
                "best-for": "Decoupled systems, real-time, integration scenarios",
                "avoid-when": "Strong consistency, simple request-response patterns",
            },
            "pipeline": {
                "trade-off": "Stage coupling, error handling, state management",
                "mitigation": "Idempotent stages, checkpointing, clear error paths",
                "best-for": "ETL workflows, data processing, transformations",
                "avoid-when": "Non-linear processing, complex branching logic",
            },
            "serverless": {
                "trade-off": "Cold starts, vendor lock-in, execution limits",
                "mitigation": "Provisioned concurrency, abstract providers, local test",
                "best-for": "Variable workloads, rapid development, cost savings",
                "avoid-when": "Long-running processes, low-latency, complex state",
            },
            "space-based": {
                "trade-off": "Memory costs, replication complexity, partitioning",
                "mitigation": "Capacity planning, data aging, eventual consistency",
                "best-for": "Extreme scalability, in-memory, high throughput",
                "avoid-when": "Limited memory, strong consistency, small scale",
            },
            "microkernel": {
                "trade-off": "Plugin interface versioning, core stability needs",
                "mitigation": "Semantic versioning, backwards compatibility testing",
                "best-for": "Extensible platforms, customization, plugin systems",
                "avoid-when": "Stable feature set, no extensibility requirements",
            },
            "service-based": {
                "trade-off": "Service granularity, shared database challenges",
                "mitigation": "Clear contracts, consider database-per-service",
                "best-for": "SOA migration, coarse services, enterprise integration",
                "avoid-when": "Fine-grained independence, startup/greenfield",
            },
            "client-server": {
                "trade-off": "Single point of failure, scalability limits, coupling",
                "mitigation": "Load balancing, caching strategies, API versioning",
                "best-for": "Simple applications, internal tools, prototypes",
                "avoid-when": "High scalability needed, offline-first requirements",
            },
        }

        return trade_offs.get(
            paradigm,
            {
                "trade-off": "Unknown paradigm-specific trade-offs",
                "mitigation": "Research paradigm-specific challenges",
                "best-for": "Specific use cases",
                "avoid-when": "Use case doesn't match paradigm strengths",
            },
        )

    def _generate_alternatives(self, selected: str) -> list[dict[str, str]]:
        """Generate alternative paradigms that were considered.

        Args:
            selected: The paradigm that was selected

        Returns:
            List of alternative paradigms with rejection reasons

        """
        all_paradigms = [
            "layered",
            "hexagonal",
            "functional-core",
            "modular-monolith",
            "microservices",
            "service-based",
            "event-driven",
            "cqrs-es",
            "serverless",
            "space-based",
            "pipeline",
            "microkernel",
            "client-server",
        ]

        # Prioritize related paradigms for comparison
        related_paradigms = self._get_related_paradigms(selected)

        alternatives = []
        # First add related paradigms
        for paradigm in related_paradigms:
            if paradigm != selected and paradigm in all_paradigms:
                alternatives.append(
                    {
                        "paradigm": paradigm,
                        "reason": self._rejection_reason(paradigm, selected),
                    }
                )

        # Then add other paradigms
        for paradigm in all_paradigms:
            if paradigm != selected and paradigm not in related_paradigms:
                alternatives.append(
                    {
                        "paradigm": paradigm,
                        "reason": self._rejection_reason(paradigm, selected),
                    }
                )

        return alternatives[:3]  # Top 3 alternatives

    def _get_related_paradigms(self, paradigm: str) -> list[str]:
        """Get paradigms related to the selected one for comparison.

        Args:
            paradigm: Selected paradigm

        Returns:
            List of related paradigm names

        """
        relations = {
            "layered": ["hexagonal", "modular-monolith", "client-server"],
            "hexagonal": ["layered", "functional-core", "modular-monolith"],
            "functional-core": ["hexagonal", "layered", "cqrs-es"],
            "modular-monolith": ["microservices", "service-based", "layered"],
            "microservices": ["modular-monolith", "service-based", "event-driven"],
            "service-based": ["microservices", "modular-monolith", "layered"],
            "event-driven": ["microservices", "cqrs-es", "pipeline"],
            "cqrs-es": ["event-driven", "functional-core", "hexagonal"],
            "serverless": ["microservices", "event-driven", "pipeline"],
            "space-based": ["microservices", "event-driven", "cqrs-es"],
            "pipeline": ["event-driven", "serverless", "layered"],
            "microkernel": ["modular-monolith", "hexagonal", "layered"],
            "client-server": ["layered", "modular-monolith", "service-based"],
        }
        return relations.get(paradigm, ["layered", "hexagonal", "microservices"])

    def _rejection_reason(self, rejected: str, selected: str) -> str:
        """Generate reason why a paradigm was rejected.

        Args:
            rejected: The rejected paradigm
            selected: The selected paradigm

        Returns:
            Rejection reason string

        """
        reasons = {
            # Layered rejections
            ("layered", "hexagonal"): "Less flexible for infrastructure changes",
            (
                "layered",
                "functional-core",
            ): "Poor separation of business logic from I/O",
            ("layered", "modular-monolith"): "Weak module boundaries for team size",
            (
                "layered",
                "microservices",
            ): "Insufficient isolation for distributed teams",
            # Hexagonal rejections
            ("hexagonal", "layered"): "Excessive abstraction for simple requirements",
            ("hexagonal", "functional-core"): "Mutable state complicates testing",
            ("hexagonal", "microservices"): "Single deployment may not scale",
            # Functional-core rejections
            ("functional-core", "layered"): "Overkill for simple CRUD operations",
            (
                "functional-core",
                "hexagonal",
            ): "Functional patterns may be unfamiliar to team",
            (
                "functional-core",
                "cqrs-es",
            ): "Event sourcing adds unnecessary complexity",
            # Modular-monolith rejections
            ("modular-monolith", "layered"): "Insufficient boundaries for growing team",
            (
                "modular-monolith",
                "microservices",
            ): "Independent deployment not yet needed",
            (
                "modular-monolith",
                "service-based",
            ): "Distribution adds operational overhead",
            # Microservices rejections
            (
                "microservices",
                "modular-monolith",
            ): "Distributed complexity not justified for team size",
            (
                "microservices",
                "service-based",
            ): "Fine-grained services add coordination overhead",
            ("microservices", "serverless"): "Container management offers more control",
            # Service-based rejections
            (
                "service-based",
                "microservices",
            ): "Coarse services may not scale independently",
            (
                "service-based",
                "modular-monolith",
            ): "Distribution adds latency without clear benefit",
            # Event-driven rejections
            (
                "event-driven",
                "microservices",
            ): "Synchronous communication sufficient for use case",
            ("event-driven", "cqrs-es"): "Full event sourcing not needed",
            ("event-driven", "pipeline"): "Workflow-style processing not required",
            # CQRS-ES rejections
            ("cqrs-es", "layered"): "Audit requirements don't justify CQRS complexity",
            ("cqrs-es", "event-driven"): "Full event sourcing adds maintenance burden",
            ("cqrs-es", "hexagonal"): "Simpler read/write patterns sufficient",
            # Serverless rejections
            ("serverless", "microservices"): "Cold starts impact latency requirements",
            ("serverless", "event-driven"): "Vendor lock-in concerns",
            ("serverless", "pipeline"): "Long-running processes not supported",
            # Space-based rejections
            ("space-based", "microservices"): "Memory costs prohibitive for workload",
            ("space-based", "event-driven"): "Extreme scalability not required",
            (
                "space-based",
                "cqrs-es",
            ): "In-memory processing overkill for consistency needs",
            # Pipeline rejections
            ("pipeline", "event-driven"): "Streaming not required, batch sufficient",
            ("pipeline", "serverless"): "Long-running stages need persistent compute",
            ("pipeline", "layered"): "Linear processing model too rigid",
            # Microkernel rejections
            (
                "microkernel",
                "modular-monolith",
            ): "Plugin architecture adds API overhead",
            ("microkernel", "hexagonal"): "Extensibility not a primary requirement",
            ("microkernel", "layered"): "Core/plugin separation not needed",
            # Client-server rejections
            ("client-server", "layered"): "Scalability limits apparent",
            ("client-server", "microservices"): "Single server bottleneck expected",
            ("client-server", "modular-monolith"): "Tighter coupling than alternatives",
        }

        return reasons.get(
            (rejected, selected), f"{selected} better fits current context"
        )

    def save_research_session(self, output_path: Path) -> None:
        """Save research session to JSON for later reference.

        Args:
            output_path: Path to save session data

        """
        session_data = {
            "context": {
                "project_type": self.context.project_type,
                "domain_complexity": self.context.domain_complexity,
                "team_size": self.context.team_size,
                "language": self.context.language,
            },
            "search_queries": self.generate_search_queries(),
            "research_results": self.research_results,
        }

        output_path.write_text(json.dumps(session_data, indent=2))


def parse_project_context(user_input: dict[str, str]) -> ProjectContext:
    """Parse user input into ProjectContext.

    Args:
        user_input: Dictionary of user-provided context

    Returns:
        ProjectContext object

    """
    return ProjectContext(
        project_type=user_input.get("project_type", "web-application"),
        domain_complexity=user_input.get("domain_complexity", "moderate"),
        team_size=user_input.get("team_size", "5-15"),
        team_experience=user_input.get("team_experience", "mixed"),
        team_distribution=user_input.get("team_distribution", "remote"),
        language=user_input.get("language", "python"),
        framework=user_input.get("framework", ""),
        scalability_needs=user_input.get("scalability_needs", "moderate"),
        security_requirements=user_input.get("security_requirements", "standard"),
        integration_points=user_input.get("integration_points", "").split(", ")
        if user_input.get("integration_points")
        else [],
        time_to_market=user_input.get("time_to_market", "normal"),
        constraints=user_input.get("constraints", "").split(", ")
        if user_input.get("constraints")
        else [],
    )


def main():
    """CLI entry point for architecture researcher."""
    parser = argparse.ArgumentParser(
        description="Architecture paradigm recommendation based on project context"
    )
    parser.add_argument(
        "--project-type",
        default="web-application",
        choices=[
            "web-api",
            "web-application",
            "cli-tool",
            "data-pipeline",
            "library",
            "microservice",
            "mobile-backend",
            "desktop-app",
            "embedded",
            "ml-system",
        ],
        help="Type of project being built",
    )
    parser.add_argument(
        "--domain-complexity",
        default="moderate",
        choices=["simple", "moderate", "complex", "highly-complex"],
        help="Complexity of the business domain",
    )
    parser.add_argument(
        "--team-size",
        default="5-15",
        choices=["<5", "5-15", "15-50", "50+"],
        help="Size of the development team",
    )
    parser.add_argument(
        "--language",
        default="python",
        choices=["python", "rust", "typescript"],
        help="Primary programming language",
    )
    parser.add_argument(
        "--framework",
        default="",
        help="Framework being used (optional)",
    )
    parser.add_argument(
        "--scalability-needs",
        default="moderate",
        choices=["low", "moderate", "high", "extreme"],
        help="Scalability requirements",
    )
    parser.add_argument(
        "--security-requirements",
        default="standard",
        choices=["standard", "high", "critical"],
        help="Security requirements level",
    )
    parser.add_argument(
        "--output-json",
        action="store_true",
        help="Output recommendation as JSON",
    )
    parser.add_argument(
        "--save-session",
        type=str,
        help="Save research session to specified JSON file",
    )

    args = parser.parse_args()

    # Build context from arguments
    context = parse_project_context(
        {
            "project_type": args.project_type,
            "domain_complexity": args.domain_complexity,
            "team_size": args.team_size,
            "language": args.language,
            "framework": args.framework,
            "scalability_needs": args.scalability_needs,
            "security_requirements": args.security_requirements,
        }
    )

    researcher = ArchitectureResearcher(context)
    recommendation = researcher.recommend_paradigm()

    if args.output_json:
        output = {
            "primary": recommendation.primary,
            "secondary": recommendation.secondary,
            "rationale": recommendation.rationale,
            "trade_offs": recommendation.trade_offs,
            "alternatives": recommendation.alternatives,
            "confidence": recommendation.confidence,
        }
        print(json.dumps(output, indent=2))
    else:
        print("=" * 60)
        print("Architecture Recommendation")
        print("=" * 60)
        print(f"\nPrimary Paradigm: {recommendation.primary}")
        if recommendation.secondary:
            print(f"Secondary Paradigm: {recommendation.secondary}")
        print(f"Confidence: {recommendation.confidence.upper()}")
        print(f"\nRationale:\n{recommendation.rationale}")

        if recommendation.trade_offs:
            print("\nTrade-offs:")
            for key, value in recommendation.trade_offs.items():
                print(f"  - {key}: {value}")

        if recommendation.alternatives:
            print("\nAlternatives Considered:")
            for alt in recommendation.alternatives[:3]:
                print(f"  - {alt['paradigm']}: {alt['reason']}")

    if args.save_session:
        researcher.save_research_session(Path(args.save_session))
        print(f"\nSession saved to: {args.save_session}")


if __name__ == "__main__":
    main()
