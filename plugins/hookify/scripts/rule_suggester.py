#!/usr/bin/env python3
"""Context-aware hookify rule suggestions.

Analyzes project context and suggests relevant hookify rules based on:
- Programming languages detected
- Project structure (monorepo, library, app)
- Git configuration
- Existing tooling (linters, formatters)

Usage:
    python rule_suggester.py [--project-dir <path>] [--format json|text]
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ProjectContext:
    """Detected project context."""

    languages: list[str] = field(default_factory=list)
    has_git: bool = False
    has_docker: bool = False
    has_ci: bool = False
    frameworks: list[str] = field(default_factory=list)
    package_managers: list[str] = field(default_factory=list)
    project_type: str = "unknown"  # app, library, monorepo


@dataclass
class RuleSuggestion:
    """A suggested hookify rule."""

    name: str
    description: str
    relevance: float  # 0-1 score
    reason: str
    rule_template: str
    category: str  # security, quality, workflow


# Built-in rule templates for common scenarios
RULE_TEMPLATES = {
    "python": [
        RuleSuggestion(
            name="block-pip-install-untrusted",
            description="Block pip install from untrusted sources",
            relevance=0.9,
            reason="Python project detected",
            category="security",
            rule_template="""---
name: block-pip-install-untrusted
event: bash
pattern: 'pip install.*--trusted-host|pip install.*http://'
action: block
---
Blocked: Installing from untrusted sources. Use HTTPS or verified packages.""",
        ),
        RuleSuggestion(
            name="warn-no-venv",
            description="Warn when installing packages outside venv",
            relevance=0.7,
            reason="Python project detected",
            category="quality",
            rule_template="""---
name: warn-no-venv
event: bash
conditions:
  - field: command
    operator: contains
    pattern: pip install
  - field: command
    operator: not_contains
    pattern: uv
action: warn
---
Consider using a virtual environment or uv for package management.""",
        ),
    ],
    "javascript": [
        RuleSuggestion(
            name="block-npm-audit-bypass",
            description="Block npm install with audit disabled",
            relevance=0.85,
            reason="JavaScript project detected",
            category="security",
            rule_template="""---
name: block-npm-audit-bypass
event: bash
pattern: 'npm install.*--no-audit|npm i.*--ignore-scripts'
action: block
---
Blocked: Security audits should not be bypassed.""",
        ),
    ],
    "git": [
        RuleSuggestion(
            name="block-force-push-main",
            description="Block force push to main/master",
            relevance=0.95,
            reason="Git repository detected",
            category="security",
            rule_template="""---
name: block-force-push-main
event: bash
pattern: 'git push.*(--force|-f).*(main|master)'
action: block
---
Blocked: Force pushing to main/master can cause data loss. Use --force-with-lease or create a PR.""",
        ),
        RuleSuggestion(
            name="warn-commit-no-message",
            description="Warn on commits without meaningful message",
            relevance=0.7,
            reason="Git repository detected",
            category="quality",
            rule_template="""---
name: warn-commit-no-message
event: bash
pattern: 'git commit.*-m\\s*["\\'](fix|wip|tmp|test)["\\'\\s]*$'
action: warn
---
Consider using a more descriptive commit message.""",
        ),
    ],
    "docker": [
        RuleSuggestion(
            name="warn-docker-latest",
            description="Warn when using :latest tag",
            relevance=0.8,
            reason="Docker detected",
            category="quality",
            rule_template="""---
name: warn-docker-latest
event: bash
pattern: 'docker (pull|run).*:latest'
action: warn
---
Consider pinning to a specific version instead of :latest for reproducibility.""",
        ),
    ],
}


def detect_context(project_dir: Path) -> ProjectContext:
    """Detect project context from directory structure.

    Args:
        project_dir: Project root directory

    Returns:
        ProjectContext with detected information
    """
    ctx = ProjectContext()

    # Detect Git
    if (project_dir / ".git").exists():
        ctx.has_git = True

    # Detect Docker
    if (project_dir / "Dockerfile").exists() or (
        project_dir / "docker-compose.yml"
    ).exists():
        ctx.has_docker = True

    # Detect CI
    ci_dirs = [".github/workflows", ".gitlab-ci.yml", ".circleci", "Jenkinsfile"]
    ctx.has_ci = any((project_dir / ci).exists() for ci in ci_dirs)

    # Detect Python
    py_markers = ["pyproject.toml", "setup.py", "requirements.txt", "Pipfile"]
    if any((project_dir / m).exists() for m in py_markers):
        ctx.languages.append("python")
        if (project_dir / "pyproject.toml").exists():
            ctx.package_managers.append("uv/pip")

    # Detect JavaScript/TypeScript
    js_markers = ["package.json", "yarn.lock", "pnpm-lock.yaml"]
    if any((project_dir / m).exists() for m in js_markers):
        ctx.languages.append("javascript")
        if (project_dir / "tsconfig.json").exists():
            ctx.languages.append("typescript")

    # Detect Rust
    if (project_dir / "Cargo.toml").exists():
        ctx.languages.append("rust")

    # Detect Go
    if (project_dir / "go.mod").exists():
        ctx.languages.append("go")

    # Determine project type
    if (project_dir / "packages").is_dir() or (project_dir / "apps").is_dir():
        ctx.project_type = "monorepo"
    elif any((project_dir / m).exists() for m in ["src/lib.rs", "src/__init__.py"]):
        ctx.project_type = "library"
    else:
        ctx.project_type = "app"

    return ctx


def suggest_rules(ctx: ProjectContext) -> list[RuleSuggestion]:
    """Suggest hookify rules based on project context.

    Args:
        ctx: Detected project context

    Returns:
        List of suggested rules sorted by relevance
    """
    suggestions = []

    # Always suggest git rules if git detected
    if ctx.has_git:
        suggestions.extend(RULE_TEMPLATES["git"])

    # Language-specific rules
    for lang in ctx.languages:
        if lang in RULE_TEMPLATES:
            suggestions.extend(RULE_TEMPLATES[lang])

    # Docker rules
    if ctx.has_docker:
        suggestions.extend(RULE_TEMPLATES["docker"])

    # Sort by relevance
    suggestions.sort(key=lambda s: s.relevance, reverse=True)

    return suggestions


def format_suggestions(
    suggestions: list[RuleSuggestion], ctx: ProjectContext, fmt: str = "text"
) -> str:
    """Format suggestions for output.

    Args:
        suggestions: List of rule suggestions
        ctx: Project context
        fmt: Output format (text or json)

    Returns:
        Formatted output string
    """
    if fmt == "json":
        return json.dumps(
            {
                "context": {
                    "languages": ctx.languages,
                    "has_git": ctx.has_git,
                    "has_docker": ctx.has_docker,
                    "project_type": ctx.project_type,
                },
                "suggestions": [
                    {
                        "name": s.name,
                        "description": s.description,
                        "relevance": s.relevance,
                        "reason": s.reason,
                        "category": s.category,
                    }
                    for s in suggestions
                ],
            },
            indent=2,
        )

    lines = [
        "# Hookify Rule Suggestions",
        "",
        f"**Project type**: {ctx.project_type}",
        f"**Languages**: {', '.join(ctx.languages) or 'none detected'}",
        f"**Git**: {'yes' if ctx.has_git else 'no'}",
        f"**Docker**: {'yes' if ctx.has_docker else 'no'}",
        "",
        f"## Suggested Rules ({len(suggestions)})",
        "",
    ]

    for s in suggestions:
        lines.extend(
            [
                f"### {s.name}",
                f"**Relevance**: {s.relevance:.0%} | **Category**: {s.category}",
                f"**Reason**: {s.reason}",
                "",
                "```yaml",
                s.rule_template,
                "```",
                "",
            ]
        )

    return "\n".join(lines)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Suggest hookify rules based on project context"
    )
    parser.add_argument(
        "--project-dir",
        "-d",
        type=Path,
        default=Path.cwd(),
        help="Project directory to analyze",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    parser.add_argument(
        "--min-relevance",
        type=float,
        default=0.5,
        help="Minimum relevance score (0-1)",
    )

    args = parser.parse_args()

    ctx = detect_context(args.project_dir)
    suggestions = suggest_rules(ctx)

    # Filter by relevance
    suggestions = [s for s in suggestions if s.relevance >= args.min_relevance]

    output = format_suggestions(suggestions, ctx, args.format)
    print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
