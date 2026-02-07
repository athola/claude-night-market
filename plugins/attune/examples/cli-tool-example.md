# CLI Tool Example: File Organizer

This example demonstrates architecture-aware initialization for a command-line tool.

## Project Scenario

**Project**: File Organizer CLI
**Team**: 3 developers (small team)
**Requirements**:
- Organize files by type, date, or custom rules
- Support for plugins to add new organization strategies
- Configuration file support
- Dry-run mode for safety
- Progress reporting for large directories

## Workflow

### Step 1: Architecture-Aware Initialization

```bash
/attune:arch-init --name file-organizer
```

### Interactive Session

```
============================================================
Architecture-Aware Project Initialization
============================================================

Project Context
------------------------------------------------------------

Project Type:
  1. web-api
  2. web-application
  3. cli-tool
  ...

Select project type (1-10) or enter custom: 3

Domain Complexity:
  1. Simple
  2. Moderate
  3. Complex
  4. Highly-Complex

Select complexity (1-4): 2

Team Size:
  1. < 5
  2. 5-15
  3. 15-50
  4. 50+

Select team size (1-4): 1

Programming Language:
  1. Python
  2. Rust
  3. TypeScript

Select language (1-3): 1

Framework (optional, press Enter to skip): click

Scalability Needs: 1 (Low)
Security Requirements: 1 (Standard)
Time to Market: 2 (Normal)
```

### Research Phase

```
============================================================
Online Research Phase
============================================================

Generated search queries for your project context:
------------------------------------------------------------

1. cli-tool architecture best practices 2026
   Command: WebSearch("cli-tool architecture best practices 2026")

2. python cli-tool architecture patterns 2026
   Command: WebSearch("python cli-tool architecture patterns 2026")

3. click architecture patterns cli-tool
   Command: WebSearch("click architecture patterns cli-tool")

------------------------------------------------------------

Research Focus Areas:
------------------------------------------------------------

  Industry Standards:
    Current architecture patterns for cli-tool in 2026

  Language Patterns:
    Python-specific best practices and idioms

  Framework Integration:
    Click architecture patterns and conventions

  Collaboration Patterns:
    Module ownership and code review strategies
```

### Recommendation

```
============================================================
Architecture Recommendation
============================================================

Primary Paradigm: **Layered**
Secondary Paradigm: Hexagonal

Confidence: HIGH

Rationale:
**Selected Based On**: matrix selection
**Team Size**: <5
**Domain Complexity**: moderate
**Project Type**: cli-tool

Trade-offs:
  - **trade-off**: Can lead to anemic domain models and tight layer coupling
  - **mitigation**: Ensure business logic stays in service layer, use DTOs at boundaries
  - **best-for**: Teams new to architecture patterns, CRUD-heavy applications
  - **avoid-when**: Complex domain logic or frequent infrastructure changes expected

Alternatives Considered:
  - **Hexagonal**: Excessive abstraction for simple requirements
  - **Modular Monolith**: Weak module boundaries for team size
  - **Client Server**: Scalability limits apparent

============================================================

Accept this recommendation? [y/n]: y
```

### Template Customization

```
============================================================
Customizing Templates
============================================================

Architecture: Layered Architecture - traditional N-tier separation
```

### Project Creation

```
============================================================
Creating Project Structure
============================================================

Created: .gitignore
Created: .pre-commit-config.yaml
Created: Makefile
Created: pyproject.toml
Created: .github/workflows/test.yml
Created: .github/workflows/lint.yml
Created: .github/workflows/typecheck.yml
Created: src/file_organizer/__init__.py
Created: tests/__init__.py

Created 3 architecture-specific directories

============================================================
Generating Documentation
============================================================

Created: ARCHITECTURE.md
Created: docs/adr/001-architecture-paradigm.md
Created: .attune/arch-init-session.json
```

### Completion

```
============================================================
Architecture-Aware Initialization Complete!
============================================================

Project: file-organizer
Architecture: Layered

Created 10 files
Created 3 architecture-specific directories

Documentation:
  - ARCHITECTURE.md - Architecture overview
  - docs/adr/001-architecture-paradigm.md - Decision record

Next Steps:
  1. cd file-organizer
  2. make dev-setup
  3. Review ARCHITECTURE.md for implementation guidance
  4. Load paradigm skill: Skill(architecture-paradigm-layered)

============================================================
```

## Generated Project Structure

```
file-organizer/
├── .attune/
│   └── arch-init-session.json
├── .github/
│   └── workflows/
│       ├── test.yml
│       ├── lint.yml
│       └── typecheck.yml
├── docs/
│   └── adr/
│       └── 001-architecture-paradigm.md
├── src/
│   └── file_organizer/
│       ├── presentation/           # CLI interface
│       │   ├── __init__.py
│       │   ├── api.py             # Click commands
│       │   └── views.py           # Output formatting
│       ├── business/              # Core logic
│       │   ├── __init__.py
│       │   ├── services.py        # Organization services
│       │   └── models.py          # File models
│       ├── data/                  # I/O operations
│       │   ├── __init__.py
│       │   ├── repositories.py    # File system access
│       │   └── models.py          # Data models
│       └── __init__.py
├── tests/
│   └── __init__.py
├── .gitignore
├── .pre-commit-config.yaml
├── ARCHITECTURE.md
├── Makefile
├── pyproject.toml
└── README.md
```

## Implementation Guidance

### Presentation Layer (CLI Interface)

```python
# src/file_organizer/presentation/api.py
import click
from file_organizer.business.services import OrganizationService

@click.group()
def cli():
    """File Organizer - Organize your files intelligently."""
    pass

@cli.command()
@click.argument('source', type=click.Path(exists=True))
@click.option('--target', '-t', type=click.Path(), help='Target directory')
@click.option('--strategy', '-s', default='type', help='Organization strategy')
@click.option('--dry-run', is_flag=True, help='Show what would be done')
def organize(source: str, target: str, strategy: str, dry_run: bool):
    """Organize files in SOURCE directory."""
    service = OrganizationService()
    result = service.organize(source, target, strategy, dry_run)
    click.echo(result.summary())
```

### Business Layer (Core Logic)

```python
# src/file_organizer/business/services.py
from dataclasses import dataclass
from pathlib import Path
from file_organizer.business.models import OrganizationResult
from file_organizer.data.repositories import FileRepository

@dataclass
class OrganizationService:
    """Service for organizing files."""

    repository: FileRepository = None

    def __post_init__(self):
        self.repository = self.repository or FileRepository()

    def organize(
        self,
        source: str,
        target: str,
        strategy: str,
        dry_run: bool
    ) -> OrganizationResult:
        """Organize files from source to target using strategy."""
        files = self.repository.list_files(Path(source))
        actions = self._plan_actions(files, target, strategy)

        if not dry_run:
            self.repository.execute_actions(actions)

        return OrganizationResult(actions=actions, dry_run=dry_run)
```

### Data Layer (File Operations)

```python
# src/file_organizer/data/repositories.py
from pathlib import Path
from typing import List
from file_organizer.data.models import FileInfo, FileAction

class FileRepository:
    """Repository for file system operations."""

    def list_files(self, directory: Path) -> List[FileInfo]:
        """List all files in directory recursively."""
        return [
            FileInfo.from_path(p)
            for p in directory.rglob('*')
            if p.is_file()
        ]

    def execute_actions(self, actions: List[FileAction]) -> None:
        """Execute file organization actions."""
        for action in actions:
            action.source.rename(action.target)
```

## Why Layered Architecture?

For this CLI tool project:

1. **Clear Separation**: CLI interface, business logic, and file operations stay separated
2. **Testability**: Business logic can be tested without touching the file system
3. **Simplicity**: Small team can understand and maintain the codebase easily
4. **Evolution**: Can add new commands or strategies without major restructuring

## Next Steps

After initialization:

1. **Set up development environment**:
   ```bash
   cd file-organizer
   make dev-setup
   ```

2. **Review architecture documentation**:
   - `ARCHITECTURE.md` for structure overview
   - `docs/adr/001-architecture-paradigm.md` for decision rationale

3. **Load implementation guidance**:
   ```bash
   Skill(architecture-paradigm-layered)
   ```

4. **Continue with specification**:
   ```bash
   /attune:specify
   /attune:blueprint
   /attune:execute
   ```

## Alternative Approach: Microkernel

If the CLI tool requires plugin extensibility as a primary feature, consider:

```bash
/attune:arch-init --name file-organizer --arch microkernel
```

This would generate:

```
file-organizer/
├── src/
│   └── file_organizer/
│       ├── core/                  # Plugin kernel
│       │   ├── kernel.py
│       │   ├── plugin_manager.py
│       │   └── registry.py
│       ├── plugins/               # Plugin implementations
│       │   ├── base.py
│       │   └── type_organizer/    # Built-in plugin
│       │       └── plugin.py
│       └── api/                   # CLI and plugin API
│           ├── plugin_api.py
│           └── core_api.py
```

This structure allows third-party plugins to add organization strategies.
