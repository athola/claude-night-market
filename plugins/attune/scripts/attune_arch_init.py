#!/usr/bin/env python3
"""Architecture-aware project initialization combining research and archetype selection."""

import argparse
import sys
from pathlib import Path

from architecture_researcher import (
    ArchitectureResearcher,
    parse_project_context,
)
from attune_init import (
    copy_templates,
    create_project_structure,
    get_default_variables,
    initialize_git,
)
from project_detector import ProjectDetector
from template_customizer import TemplateCustomizer


def interactive_context_gathering() -> dict[str, str]:
    """Gather project context interactively from user.

    Returns:
        Dictionary of project context
    """
    print("\n" + "=" * 60)
    print("Architecture-Aware Project Initialization")
    print("=" * 60)

    context = {}

    print("\n📋 Project Context")
    print("-" * 60)

    # Project type
    project_types = [
        "web-api",
        "web-application",
        "cli-tool",
        "data-pipeline",
        "library",
        "microservice",
        "desktop-app",
        "mobile-app",
        "real-time-system",
        "streaming-app",
    ]
    print("\nProject Type:")
    for i, pt in enumerate(project_types, 1):
        print(f"  {i}. {pt}")

    while True:
        choice = input("\nSelect project type (1-10) or enter custom: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(project_types):
            context["project_type"] = project_types[int(choice) - 1]
            break
        elif choice:
            context["project_type"] = choice
            break

    # Domain complexity
    complexities = ["simple", "moderate", "complex", "highly-complex"]
    print("\nDomain Complexity:")
    for i, comp in enumerate(complexities, 1):
        print(f"  {i}. {comp.title()}")

    while True:
        choice = input("\nSelect complexity (1-4): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= 4:
            context["domain_complexity"] = complexities[int(choice) - 1]
            break

    # Team size
    team_sizes = ["<5", "5-15", "15-50", "50+"]
    print("\nTeam Size:")
    for i, ts in enumerate(team_sizes, 1):
        print(f"  {i}. {ts}")

    while True:
        choice = input("\nSelect team size (1-4): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= 4:
            context["team_size"] = team_sizes[int(choice) - 1]
            break

    # Language
    languages = ["python", "rust", "typescript"]
    print("\nProgramming Language:")
    for i, lang in enumerate(languages, 1):
        print(f"  {i}. {lang.title()}")

    while True:
        choice = input("\nSelect language (1-3): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= 3:
            context["language"] = languages[int(choice) - 1]
            break

    # Optional: Framework
    framework = input("\nFramework (optional, press Enter to skip): ").strip()
    if framework:
        context["framework"] = framework
    else:
        context["framework"] = ""

    # Scalability needs
    print("\nScalability Needs:")
    print("  1. Low (< 1000 users)")
    print("  2. Moderate (< 100K users)")
    print("  3. High (< 1M users)")
    print("  4. Extreme (> 1M users)")

    choice = input("\nSelect scalability (1-4, default 2): ").strip()
    scalability_map = {"1": "low", "2": "moderate", "3": "high", "4": "extreme"}
    context["scalability_needs"] = scalability_map.get(choice, "moderate")

    # Security requirements
    print("\nSecurity Requirements:")
    print("  1. Standard")
    print("  2. High")
    print("  3. Critical (finance, health, etc.)")

    choice = input("\nSelect security level (1-3, default 1): ").strip()
    security_map = {"1": "standard", "2": "high", "3": "critical"}
    context["security_requirements"] = security_map.get(choice, "standard")

    # Time to market
    print("\nTime to Market:")
    print("  1. Rapid (ASAP)")
    print("  2. Normal")
    print("  3. Not Urgent")

    choice = input("\nSelect timeline (1-3, default 2): ").strip()
    time_map = {"1": "rapid", "2": "normal", "3": "not-urgent"}
    context["time_to_market"] = time_map.get(choice, "normal")

    return context


def present_recommendation(recommendation) -> bool:
    """Present architecture recommendation to user for confirmation.

    Args:
        recommendation: ArchitectureRecommendation object

    Returns:
        True if user accepts recommendation
    """
    print("\n" + "=" * 60)
    print("🎯 Architecture Recommendation")
    print("=" * 60)

    print(f"\nPrimary Paradigm: **{recommendation.primary.replace('-', ' ').title()}**")
    if recommendation.secondary:
        print(
            f"Secondary Paradigm: {recommendation.secondary.replace('-', ' ').title()}"
        )

    print(f"\nConfidence: {recommendation.confidence.upper()}")

    print("\n📝 Rationale:")
    print(recommendation.rationale)

    if recommendation.trade_offs:
        print("\n⚖️  Trade-offs:")
        for key, value in recommendation.trade_offs.items():
            print(f"  - **{key}**: {value}")

    if recommendation.alternatives:
        print("\n🔄 Alternatives Considered:")
        for alt in recommendation.alternatives[:3]:
            print(
                f"  - **{alt['paradigm'].replace('-', ' ').title()}**: {alt['reason']}"
            )

    print("\n" + "=" * 60)

    while True:
        response = input("\nAccept this recommendation? [y/n]: ").strip().lower()
        if response in ["y", "yes"]:
            return True
        elif response in ["n", "no"]:
            return False
        else:
            print("Please enter 'y' or 'n'")


def perform_online_research(
    queries: list[str], context: dict[str, str]
) -> dict[str, str]:
    """Perform online research using WebSearch (would be called via Claude).

    Args:
        queries: List of search queries
        context: Project context for tailored research

    Returns:
        Dictionary of research findings
    """
    print("\n" + "=" * 60)
    print("Online Research Phase")
    print("=" * 60)

    print("\nGenerated search queries for your project context:")
    print("-" * 60)

    for i, query in enumerate(queries, 1):
        print(f"\n{i}. {query}")
        print(f'   Command: WebSearch("{query}")')

    print("\n" + "-" * 60)
    print("\nResearch Focus Areas:")
    print("-" * 60)

    focus_areas = _generate_research_focus(context)
    for area, description in focus_areas.items():
        print(f"\n  {area}:")
        print(f"    {description}")

    print("\n" + "-" * 60)
    print("\nNote: In Claude Code, these queries will be executed automatically")
    print("via WebSearch to gather current best practices and recommendations.")
    print("\nProceeding with algorithmic recommendation based on decision matrix...")

    return {}


def _generate_research_focus(context: dict[str, str]) -> dict[str, str]:
    """Generate research focus areas based on project context.

    Args:
        context: Project context dictionary

    Returns:
        Dictionary of focus areas with descriptions
    """
    focus_areas = {
        "Industry Standards": f"Current architecture patterns for {context.get('project_type', 'applications')} in 2026",
        "Language Patterns": f"{context.get('language', 'Python').title()}-specific best practices and idioms",
    }

    # Add context-specific focus areas
    if context.get("domain_complexity") in ["complex", "highly-complex"]:
        focus_areas["Domain Modeling"] = (
            "Domain-driven design patterns for complex business logic"
        )

    if context.get("security_requirements") == "critical":
        focus_areas["Security Architecture"] = (
            "Security-first patterns for sensitive data handling"
        )

    if context.get("scalability_needs") in ["high", "extreme"]:
        focus_areas["Scalability Patterns"] = (
            "Horizontal scaling strategies and load distribution"
        )

    if context.get("framework"):
        focus_areas["Framework Integration"] = (
            f"{context.get('framework').title()} architecture patterns and conventions"
        )

    team_size = context.get("team_size", "5-15")
    if team_size == "50+":
        focus_areas["Team Structure"] = (
            "Conway's Law alignment and team topology patterns"
        )
    elif team_size in ["15-50", "5-15"]:
        focus_areas["Collaboration Patterns"] = (
            "Module ownership and code review strategies"
        )

    return focus_areas


def generate_research_summary(context: dict[str, str], recommendation) -> str:
    """Generate a research summary for documentation.

    Args:
        context: Project context
        recommendation: Architecture recommendation

    Returns:
        Research summary markdown string
    """
    summary = f"""## Research Summary

### Project Context Analysis

| Attribute | Value |
|-----------|-------|
| Project Type | {context.get('project_type', 'N/A')} |
| Domain Complexity | {context.get('domain_complexity', 'N/A')} |
| Team Size | {context.get('team_size', 'N/A')} |
| Language | {context.get('language', 'N/A')} |
| Scalability | {context.get('scalability_needs', 'N/A')} |
| Security | {context.get('security_requirements', 'N/A')} |

### Recommendation Basis

The **{recommendation.primary.replace('-', ' ').title()}** architecture was selected based on:

1. **Team-Domain Fit**: {context.get('team_size', 'N/A')} engineers working on {context.get('domain_complexity', 'N/A')} domain
2. **Project Requirements**: {context.get('project_type', 'N/A')} with {context.get('scalability_needs', 'N/A')} scalability needs
3. **Decision Matrix**: Algorithmic matching of context to proven architectural patterns

### Key Considerations

"""
    # Add trade-off information
    if recommendation.trade_offs:
        summary += "#### Trade-offs\n\n"
        for key, value in recommendation.trade_offs.items():
            summary += f"- **{key.replace('-', ' ').title()}**: {value}\n"

    return summary


def main():
    """Main entry point for architecture-aware initialization."""
    parser = argparse.ArgumentParser(
        description="Initialize a project with architecture awareness"
    )
    parser.add_argument("--name", help="Project name")
    parser.add_argument("--arch", "--architecture", help="Force specific architecture")
    parser.add_argument(
        "--no-research", action="store_true", help="Skip online research phase"
    )
    parser.add_argument(
        "--accept-recommendation",
        action="store_true",
        help="Auto-accept recommendation (non-interactive)",
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=Path.cwd(),
        help="Project path (defaults to current directory)",
    )

    args = parser.parse_args()

    project_path = args.path.resolve()
    project_name = args.name or project_path.name

    # Step 1: Gather context
    context_data = interactive_context_gathering()
    context_data["project_name"] = project_name

    # Step 2: Research phase (optional, would use WebSearch in production)
    context = parse_project_context(context_data)
    researcher = ArchitectureResearcher(context)

    if not args.no_research:
        queries = researcher.generate_search_queries()
        research_findings = perform_online_research(queries, context_data)
    else:
        research_findings = {}

    # Step 3: Get recommendation
    if args.arch:
        # User specified architecture directly
        paradigm = args.arch
        recommendation = researcher._build_recommendation(
            paradigm, "", "user-specified", research_findings
        )
    else:
        # Algorithmic recommendation
        recommendation = researcher.recommend_paradigm(research_findings)

    # Step 4: Present and confirm
    if not args.accept_recommendation:
        if not present_recommendation(recommendation):
            print("\n❌ Initialization cancelled by user.")
            sys.exit(0)
    else:
        print(f"\n✓ Auto-accepted: {recommendation.primary}")

    # Step 5: Customize templates based on architecture
    print("\n" + "=" * 60)
    print("🏗️  Customizing Templates")
    print("=" * 60)

    customizer = TemplateCustomizer(
        recommendation.primary, context.language, project_name
    )

    print(f"\nArchitecture: {customizer.get_paradigm_description()}")

    # Step 6: Create base project structure
    print("\n" + "=" * 60)
    print("📁 Creating Project Structure")
    print("=" * 60)

    # Initialize git
    detector = ProjectDetector(project_path)
    if not detector.check_git_initialized():
        initialize_git(project_path)

    # Get template variables
    variables = get_default_variables(
        project_name=project_name,
        language=context.language,
        author=context_data.get("author", "Your Name"),
        python_version="3.10",
        rust_edition="2021",
        package_manager="npm",
        repository="",
        description=f"A {recommendation.primary} architecture project",
    )

    # Copy base templates
    script_dir = Path(__file__).parent
    templates_root = script_dir.parent / "templates"
    created_files = copy_templates(
        language=context.language,
        project_path=project_path,
        variables=variables,
        templates_root=templates_root,
        force=False,
    )

    # Create standard structure
    create_project_structure(
        project_path, context.language, variables["PROJECT_MODULE"], project_name
    )

    # Create architecture-specific directories
    arch_dirs = customizer.create_architecture_directories(project_path)
    print(f"\n✓ Created {len(arch_dirs)} architecture-specific directories")

    # Step 7: Generate documentation
    print("\n" + "=" * 60)
    print("📚 Generating Documentation")
    print("=" * 60)

    # Create ARCHITECTURE.md
    arch_readme = project_path / "ARCHITECTURE.md"
    arch_readme.write_text(customizer.generate_architecture_readme())
    print(f"✓ Created: {arch_readme}")

    # Create ADR
    adr_dir = project_path / "docs" / "adr"
    adr_dir.mkdir(parents=True, exist_ok=True)
    adr_file = adr_dir / "001-architecture-paradigm.md"
    adr_file.write_text(customizer.generate_architecture_adr())
    print(f"✓ Created: {adr_file}")

    # Save research session
    session_file = project_path / ".attune" / "arch-init-session.json"
    session_file.parent.mkdir(parents=True, exist_ok=True)
    researcher.save_research_session(session_file)
    print(f"✓ Created: {session_file}")

    # Step 8: Summary
    print("\n" + "=" * 60)
    print("✓ Architecture-Aware Initialization Complete!")
    print("=" * 60)

    print(f"\nProject: {project_name}")
    print(f"Architecture: {recommendation.primary.replace('-', ' ').title()}")
    if recommendation.secondary:
        print(f"Secondary: {recommendation.secondary.replace('-', ' ').title()}")

    print(f"\n📁 Created {len(created_files)} files")
    print(f"📁 Created {len(arch_dirs)} architecture-specific directories")

    print("\n📚 Documentation:")
    print("  - ARCHITECTURE.md - Architecture overview")
    print("  - docs/adr/001-architecture-paradigm.md - Decision record")

    print("\n🔗 Next Steps:")
    print(f"  1. cd {project_path}")
    print("  2. make dev-setup")
    print("  3. Review ARCHITECTURE.md for implementation guidance")
    print(
        f"  4. Load paradigm skill: Skill(architecture-paradigm-{recommendation.primary})"
    )

    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
