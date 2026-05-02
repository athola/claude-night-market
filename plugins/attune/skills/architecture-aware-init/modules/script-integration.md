---
module: script-integration
category: tooling
dependencies: []
estimated_tokens: 500
---

# Script Integration

The skill is interactive by default but ships with three Python
scripts under `plugins/attune/scripts/` for automation and reuse.

## Architecture Research Script

```bash
uv run python plugins/attune/scripts/architecture_researcher.py \
  --project-type web-api \
  --domain-complexity complex \
  --team-size 5-15 \
  --language python \
  --output-json
```

Returns a recommendation with:

- Primary paradigm and rationale
- Trade-offs and mitigations
- Alternative paradigms considered
- Confidence level

## Template Customizer Script

```bash
uv run python plugins/attune/scripts/template_customizer.py \
  --paradigm cqrs-es \
  --language python \
  --project-name my-project \
  --output-dir ./my-project
```

Creates the paradigm-appropriate directory structure (e.g.,
`commands/`, `queries/`, `events/` for CQRS).

## Full Interactive Flow

```bash
# Interactive
uv run python plugins/attune/scripts/attune_arch_init.py \
  --name my-project \
  --lang python

# Non-interactive with explicit architecture
uv run python plugins/attune/scripts/attune_arch_init.py \
  --name my-project \
  --lang python \
  --arch hexagonal \
  --accept-recommendation
```

## Library Usage from Claude Code

```python
from architecture_researcher import ArchitectureResearcher, ProjectContext
from template_customizer import TemplateCustomizer
from pathlib import Path

context = ProjectContext(
    project_type="web-api",
    domain_complexity="complex",
    team_size="5-15",
    language="python",
)
researcher = ArchitectureResearcher(context)
recommendation = researcher.recommend()

customizer = TemplateCustomizer(
    paradigm=recommendation.primary,
    language="python",
    project_name="my-project",
)
customizer.apply_structure(Path("./my-project"))
```
