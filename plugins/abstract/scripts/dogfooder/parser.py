"""Makefile parsing and target analysis for the dogfooder package."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, cast

import yaml


def load_target_catalog() -> dict[str, Any]:
    """Load the Makefile target catalog from YAML data.

    Returns:
        Dictionary containing essential_targets, recommended_targets,
        convenience_targets, and skip_dirs lists.

    """
    # When imported as a package, __file__ is dogfooder/parser.py,
    # so we go up two levels to reach the plugin root, then into data/.
    script_dir = Path(__file__).parent.parent
    catalog_path = script_dir.parent / "data" / "makefile_target_catalog.yaml"

    with catalog_path.open(encoding="utf-8") as f:
        catalog = yaml.safe_load(f)
        return cast("dict[str, Any]", catalog)


class DocumentationCommandExtractor:
    """Extract documented commands from READMEs and documentation."""

    # Pattern for slash commands in documentation
    COMMAND_PATTERNS = [
        r"`/([\w-]+)(?:\s+([^\n`]+))?`",  # `/-command args`
        r"```bash\s*/([\w-]+)([^\n]*)",  # Code blocks with /-commands
        r"^\s*/([\w-]+)",  # Lines starting with /-command
        r"\[\\\?`/([\w-]+)",  # Escaped commands
    ]

    # Pattern for CLI tool invocations
    CLI_PATTERNS = [
        r"`claude\s+([^\n`]+)`",  # `claude command args`
        r"```bash\s+claude\s+([^\n]+)",  # Code blocks
    ]

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir

    def extract_from_file(self, filepath: Path) -> list[dict[str, Any]]:
        """Extract commands from a single file."""
        commands = []
        seen: set[tuple[str, int, str]] = set()  # (command/invocation, line, type)
        content = filepath.read_text()

        # Extract slash commands
        for pattern in self.COMMAND_PATTERNS:
            for match in re.finditer(pattern, content, re.MULTILINE):
                cmd = match.group(1)
                args = match.group(2) if len(match.groups()) > 1 else ""
                line_num = content[: match.start()].count("\n") + 1
                cmd_key = (cmd, line_num, "slash-command")

                if cmd_key not in seen:
                    seen.add(cmd_key)
                    commands.append(
                        {
                            "type": "slash-command",
                            "command": cmd,
                            "args": args.strip() if args else "",
                            "source": str(filepath.relative_to(self.root_dir)),
                            "line": line_num,
                        }
                    )

        # Extract CLI invocations
        for pattern in self.CLI_PATTERNS:
            for match in re.finditer(pattern, content, re.MULTILINE):
                invocation = match.group(1)
                line_num = content[: match.start()].count("\n") + 1
                inv_key = (invocation.strip(), line_num, "cli-invocation")

                if inv_key not in seen:
                    seen.add(inv_key)
                    commands.append(
                        {
                            "type": "cli-invocation",
                            "invocation": invocation.strip(),
                            "source": str(filepath.relative_to(self.root_dir)),
                            "line": line_num,
                        }
                    )

        return commands

    def extract_all(self) -> dict[str, list[dict[str, Any]]]:
        """Extract commands from ALL documentation files in the project.

        Scans comprehensively:
        - Plugin READMEs
        - Plugin documentation (docs/, guides/, tutorials/, examples/)
        - Root docs/
        - Wiki/ if present
        - Any .md files with command examples
        """
        results: dict[str, list[dict[str, Any]]] = {}
        seen_files: set[Path] = set()  # Track processed files to avoid duplicates

        # Documentation patterns to scan
        doc_patterns = [
            "plugins/*/README.md",
            "plugins/*/docs/**/*.md",
            "plugins/*/guides/**/*.md",
            "plugins/*/tutorials/**/*.md",
            "plugins/*/examples/**/*.md",
            "docs/**/*.md",
            "guides/**/*.md",
            "tutorials/**/*.md",
            "examples/**/*.md",
            "wiki/**/*.md",
            "**/README.md",
        ]

        # Scan all documentation patterns
        for pattern in doc_patterns:
            for doc_file in self.root_dir.glob(pattern):
                # Skip if already processed
                if doc_file in seen_files:
                    continue

                # Skip hidden files and node_modules
                if any(p.startswith(".") for p in doc_file.parts):
                    continue
                if "node_modules" in str(doc_file):
                    continue

                seen_files.add(doc_file)
                rel_path = doc_file.relative_to(self.root_dir)
                commands = self.extract_from_file(doc_file)

                if commands:
                    key = str(rel_path)
                    if key not in results:
                        results[key] = []
                    results[key].extend(commands)

        return results


class MakefileAnalyzer:
    """Analyze existing Makefile targets."""

    def __init__(self, makefile_path: Path):
        self.makefile_path = makefile_path
        self.targets = self._parse_targets()

    def _parse_targets(self) -> dict[str, dict[str, Any]]:
        """Parse targets from Makefile."""
        targets: dict[str, dict[str, Any]] = {}

        if not self.makefile_path.exists():
            return targets

        content = self.makefile_path.read_text()

        # Find target definitions
        for match in re.finditer(r"^([a-zA-Z][\w-]*)\s*:", content, re.MULTILINE):
            target_name = match.group(1)
            line_num = content[: match.start()].count("\n") + 1

            # Extract description (## comment)
            line_start = content.rfind("\n", 0, match.start()) + 1
            line_end = content.find("\n", match.start())
            line_content = content[line_start:line_end]
            description = ""

            desc_match = re.search(r"##\s*(.+)", line_content)
            if desc_match:
                description = desc_match.group(1)

            targets[target_name] = {
                "name": target_name,
                "line": line_num,
                "description": description,
            }

        return targets

    def has_target(self, target_name: str) -> bool:
        """Check if target exists."""
        return target_name in self.targets

    def get_missing_targets(self, required_targets: set[str]) -> set[str]:
        """Return set of required targets not in Makefile."""
        return required_targets - self.targets.keys()
