# Night Market for OpenClaw

142 curated skills from the [Claude Night Market][nm] ecosystem,
packaged for OpenClaw and NemoClaw users.

[nm]: https://github.com/athola/claude-night-market

## Install

```bash
# From ClawHub
openclaw skills install night-market

# Or clone and add as a local plugin
git clone https://github.com/athola/claude-night-market
cd claude-night-market/bridge/openclaw
openclaw plugin add .
```

## What's Included

| Category | Skills | Highlights |
|----------|--------|------------|
| Code Review | 12 | Bug hunting, architecture review, unified review |
| Testing | 8 | TDD workflow, test quality, Python testing |
| Documentation | 8 | Slop detection, doc generation, style learning |
| Architecture | 14 | 12 paradigm patterns, paradigm selector |
| Git Workflow | 14 | Commits, PRs, reviews, issue management |
| Conservation | 11 | Token optimization, bloat detection, context management |
| Meta-Skills | 11 | Skill authoring, evaluation, hook development |
| Project Lifecycle | 13 | Brainstorming, specification, planning, execution |

## Skill Naming

All skills are prefixed with `nm-{plugin}-` for namespace safety:

- `nm-pensive-bug-review` -- systematic bug hunting
- `nm-conserve-token-conservation` -- token budget management
- `nm-scribe-slop-detector` -- AI content quality detection
- `nm-sanctum-pr-prep` -- pull request preparation

## Full Experience

These skills are exported from Claude Code plugins.
For the complete experience with agents, hooks, commands,
and skill orchestration, install the Claude Code plugins:

```bash
claude plugin install athola/claude-night-market
```

## License

MIT -- see [LICENSE](../../LICENSE) for details.
