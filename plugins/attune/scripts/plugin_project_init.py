#!/usr/bin/env python3
"""Initialize Claude Code plugin projects with attune + abstract integration."""

import argparse
from pathlib import Path

from attune_init import copy_templates, initialize_git  # type: ignore[import]
from template_engine import get_default_variables  # type: ignore[import]


def create_plugin_structure(project_path: Path, plugin_name: str) -> None:
    """Create Claude Code plugin directory structure.

    Args:
        project_path: Path to plugin root
        plugin_name: Name of the plugin

    """
    # Create plugin directories
    dirs = [
        ".claude-plugin",
        "commands",
        "skills",
        "agents",
        "hooks",
        "scripts",
        "tests",
        "docs",
    ]

    for dir_name in dirs:
        dir_path = project_path / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created: {dir_path}")

    # Create plugin.json
    plugin_json = project_path / ".claude-plugin" / "plugin.json"
    plugin_json.write_text(f"""{{
  "name": "{plugin_name}",
  "version": "0.1.0",
  "description": "Description of {plugin_name} plugin",
  "commands": [],
  "skills": [],
  "agents": [],
  "keywords": [],
  "author": {{
    "name": "Your Name",
    "url": "https://github.com/yourusername"
  }},
  "license": "MIT"
}}
""")
    print(f"✓ Created: {plugin_json}")

    # Create metadata.json
    metadata_json = project_path / ".claude-plugin" / "metadata.json"
    metadata_json.write_text(f"""{{
  "name": "{plugin_name}",
  "version": "0.1.0",
  "description": "Description of {plugin_name} plugin",
  "category": "development-tools",
  "tags": [],
  "compatibility": {{
    "claude_code_min_version": "2.0.0"
  }}
}}
""")
    print(f"✓ Created: {metadata_json}")

    # Create README.md
    readme = project_path / "README.md"
    readme.write_text(f"""# {plugin_name.title()}

Claude Code plugin for...

## Installation

```bash
claude plugins install {plugin_name}
```

## Commands

| Command | Description |
|---------|-------------|
| `/{plugin_name}:example` | Example command |

## Skills

| Skill | Description | Use When |
|-------|-------------|----------|
| `example-skill` | Example skill | When you need... |

## Development

```bash
# Validate plugin structure
/abstract:validate-plugin {plugin_name}

# Test skills
make test

# Format code
make format
```

## License

MIT
""")
    print(f"✓ Created: {readme}")


def initialize_plugin_project(
    project_path: Path,
    plugin_name: str,
    author: str = "Your Name",
    email: str = "you@example.com",
    force: bool = False,
) -> None:
    """Initialize a Claude Code plugin project.

    Args:
        project_path: Path to project directory
        plugin_name: Name of the plugin
        author: Author name
        email: Author email
        force: Force overwrite without prompting

    """
    print(f"\n{'=' * 60}")
    print("Claude Code Plugin Project Initialization")
    print(f"{'=' * 60}")
    print(f"Plugin: {plugin_name}")
    print(f"Path: {project_path}")
    print(f"{'=' * 60}\n")

    # Initialize git
    initialize_git(project_path, force=force)

    # Create plugin structure
    create_plugin_structure(project_path, plugin_name)

    # Get template variables for Python project
    variables = get_default_variables(
        project_name=plugin_name,
        language="python",
        author=author,
        email=email,
        description=f"Claude Code plugin for {plugin_name}",
    )

    # Find templates directory
    script_dir = Path(__file__).parent
    templates_root = script_dir.parent / "templates"

    # Copy Python templates (for scripts/)
    copy_templates(
        language="python",
        project_path=project_path,
        variables=variables,
        templates_root=templates_root,
        force=force,
    )

    # Create scripts directory structure
    scripts_dir = project_path / "scripts"
    scripts_dir.mkdir(exist_ok=True)
    (scripts_dir / "__init__.py").write_text("")

    # Create tests directory structure
    tests_dir = project_path / "tests"
    tests_dir.mkdir(exist_ok=True)
    (tests_dir / "__init__.py").write_text("")

    # Create example skill
    example_skill_dir = project_path / "skills" / "example-skill"
    example_skill_dir.mkdir(parents=True, exist_ok=True)

    skill_md = example_skill_dir / "SKILL.md"
    skill_md.write_text(f"""---
name: example-skill
description: Example skill for {plugin_name} plugin
model: claude-sonnet-4
tools: [Read, Write, Bash]
---

# Example Skill

Example skill demonstrating {plugin_name} plugin capabilities.

## Use When

- Example use case 1
- Example use case 2

## Workflow

1. **Step 1**: Do something
2. **Step 2**: Do something else
3. **Step 3**: Verify results

## Examples

### Example 1

```
User: /example-command
Assistant: [executes skill]
```

## Related Skills

- `{plugin_name}:other-skill` - Related functionality
""")
    print(f"✓ Created: {skill_md}")

    # Create example command
    example_command = project_path / "commands" / "example.md"
    example_command.write_text(f"""---
name: example
description: Example command for {plugin_name} plugin
---

# Example Command

Example command demonstrating {plugin_name} plugin functionality.

## Usage

```bash
/{plugin_name}:example [args]
```

## What This Command Does

1. Step 1
2. Step 2
3. Step 3

## Examples

### Example 1

```bash
/{plugin_name}:example --option value
```

## Related Commands

- `/{plugin_name}:other` - Related command
""")
    print(f"✓ Created: {example_command}")

    # Create plugin structure test
    test_file = project_path / "tests" / "test_plugin_structure.py"
    test_file.write_text(f'''"""Test {plugin_name} plugin structure."""

import json
from pathlib import Path
import pytest


PLUGIN_ROOT = Path(__file__).parent.parent


def test_plugin_json_exists():
    """Verify plugin.json exists and is valid."""
    plugin_json = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
    assert plugin_json.exists(), "plugin.json not found"

    with open(plugin_json) as f:
        data = json.load(f)

    assert data["name"] == "{plugin_name}"
    assert "version" in data
    assert "commands" in data
    assert "skills" in data


def test_metadata_json_exists():
    """Verify metadata.json exists."""
    metadata_json = PLUGIN_ROOT / ".claude-plugin" / "metadata.json"
    assert metadata_json.exists(), "metadata.json not found"


def test_readme_exists():
    """Verify README.md exists."""
    readme = PLUGIN_ROOT / "README.md"
    assert readme.exists(), "README.md not found"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
''')
    print(f"✓ Created: {test_file}")

    print(f"\n{'=' * 60}")
    print("✓ Plugin project initialized successfully!")
    print(f"{'=' * 60}")
    print("\nNext steps:")
    print(f"  1. cd {project_path}")
    print("  2. Edit .claude-plugin/plugin.json with plugin details")
    print("  3. Create skills in skills/ directory")
    print("  4. Create commands in commands/ directory")
    print(f"  5. Validate: /abstract:validate-plugin {plugin_name}")
    print("  6. Test: make test")
    print(f"{'=' * 60}\n")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Initialize Claude Code plugin project"
    )
    parser.add_argument(
        "plugin_name",
        help="Name of the plugin",
    )
    parser.add_argument(
        "--path",
        type=Path,
        help="Project path (default: ./plugins/<plugin_name>)",
    )
    parser.add_argument(
        "--author",
        default="Your Name",
        help="Author name",
    )
    parser.add_argument(
        "--email",
        default="you@example.com",
        help="Author email",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite without prompting",
    )

    args = parser.parse_args()

    # Default path
    if args.path:
        project_path = args.path.resolve()
    else:
        project_path = Path.cwd() / "plugins" / args.plugin_name

    # Create directory if it doesn't exist
    project_path.mkdir(parents=True, exist_ok=True)

    # Initialize plugin project
    initialize_plugin_project(
        project_path=project_path,
        plugin_name=args.plugin_name,
        author=args.author,
        email=args.email,
        force=args.force,
    )


if __name__ == "__main__":
    main()
