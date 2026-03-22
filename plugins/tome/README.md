# Tome

Multi-source research plugin for Claude Code.

Tome runs autonomous research sessions across four
channels -- code repositories, community discourse,
academic literature, and cross-domain analogical
reasoning (TRIZ) -- then synthesizes findings into
domain-appropriate reports.

## Commands

| Command | Purpose |
|---------|---------|
| `/tome:research "topic"` | Start a research session |
| `/tome:dig "subtopic"` | Refine results interactively |
| `/tome:cite` | Generate bibliography |
| `/tome:export` | Export for memory-palace |

## Research Channels

**Code archaeology**: GitHub implementations via API and
WebSearch. Extracts patterns, not just links.

**Community discourse**: Hacker News (Algolia API),
Lobsters, Reddit (JSON API), and tech blogs from curated
high-quality domains.

**Academic literature**: arXiv, Semantic Scholar, with an
open-access discovery chain (Unpaywall, CORE, PubMed
Central, OpenAlex). Parses PDFs and provides fallback
guidance for paywalled content.

**TRIZ cross-domain**: Identifies adjacent fields where
analogous problems have been solved. Depth scales
dynamically from light (1 field) to maximum (5 fields
with full contradiction analysis).

## Domain Classification

Topics are classified into domains that determine TRIZ
depth, channel weights, and visualization style:

| Domain | TRIZ Depth | Example Topic |
|--------|-----------|---------------|
| ui-ux | light | "react component patterns" |
| algorithm | medium | "async python patterns" |
| architecture | medium | "microservice communication" |
| data-structure | deep | "cache eviction policy" |
| scientific | deep | "monte carlo simulation" |
| financial | medium | "portfolio risk modeling" |
| devops | light | "kubernetes deployment" |
| security | medium | "TLS certificate rotation" |

## Output Formats

- **report** (default): Full sectioned markdown
- **brief**: Condensed 1-2 pages
- **transcript**: Raw session log with bookmarks

## Skills

| Skill | Purpose |
|-------|---------|
| `research` | Pipeline orchestrator |
| `code-search` | GitHub search |
| `discourse` | Community scanning |
| `papers` | Academic literature |
| `triz` | Cross-domain analysis |
| `synthesize` | Merge and format |
| `dig` | Interactive refinement |

## Agents

| Agent | Channel |
|-------|---------|
| `code-searcher` | GitHub code search |
| `discourse-scanner` | HN, Lobsters, Reddit, blogs |
| `literature-reviewer` | arXiv, Semantic Scholar, PDFs |
| `triz-analyst` | Cross-domain analogical reasoning |

## Integration

- **memory-palace**: Export via `/tome:export` using
  knowledge-intake compatible format
- **scry**: Delegate complex visualizations
- **leyline**: Shared patterns and error handling

## Development

```bash
cd plugins/tome
uv sync --dev
uv run python -m pytest tests/ -v
```
