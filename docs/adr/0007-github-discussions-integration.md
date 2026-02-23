# ADR 0007: GitHub Discussions as Agent Collective Memory

## Status

Accepted - 2026-02-19

## Context

The claude-night-market codebase has sophisticated decision machinery (war room, scope-guard, ADRs) and knowledge management (memory-palace), but both produce artifacts stored only in local files invisible to future sessions and other contributors. Meanwhile, the leyline command-mapping table omits Discussions entirely, and the 3 `gh discussion` references in minister playbooks use CLI commands that don't exist in `gh` v2.86.0.

### Requirements

- Make agent decisions searchable and persistent via GitHub Discussions
- Enable cross-session learning by surfacing prior decisions at session start
- Bridge local knowledge (memory-palace corpus) to a public, searchable channel
- Fix the broken `gh discussion` CLI references with working GraphQL wrappers
- Structure the Discussions board with categories, form templates, and labeling conventions

### Scope

**In**: GraphQL wrapper templates (leyline), Discussion categories/forms, war room publishing (attune), session-start retrieval hook, knowledge promotion (memory-palace), scope-guard linking (imbue), minister playbook fixes, prior decision checks

**Out**: Real-time monitoring, cross-repo federation, GitLab/Bitbucket parity, embedding-based semantic search, agent-to-agent messaging, auto-publish without user consent

## Decision

Adopt a **distributed hooks + shared leyline module** architecture. Leyline provides the GraphQL foundation via command-mapping templates; each plugin owns its publishing and retrieval logic.

### Architecture

- **Leyline command-mapping** gains a Discussion Operations section with 8 GraphQL templates (list categories, create, comment, mark answer, search, get, list, update)
- **Four Discussion categories** (Decisions/Announcement, Deliberations/Open, Learnings/Open, Knowledge/Q&A) with structured YAML form templates in `.github/DISCUSSION_TEMPLATE/`
- **SessionStart hook** (`fetch-recent-discussions.sh` in leyline) queries 5 most recent Decisions discussions, bounded to `<600 tokens` and `<3 seconds`
- **Plugin integration** is self-contained: attune publishes war room decisions, memory-palace promotes evergreen knowledge, imbue links scope-guard deferrals, minister uses fixed GraphQL commands

### Key Design Choices

1. **GraphQL over REST**: GitHub has no REST API for Discussions. All operations use `gh api graphql` with parameterized variables (no string interpolation).

2. **User confirmation required**: All publishing flows prompt `[Y/n]` before creating Discussions. No auto-publish.

3. **Graceful degradation**: Non-GitHub platforms, repos without Discussions, unauthenticated `gh` -- all result in silent skip with valid empty-context JSON. The hook is best-effort enrichment, not a critical path.

4. **Category resolution by slug**: Categories are resolved at runtime via GraphQL (`discussionCategories` query) rather than hardcoding node IDs, since IDs vary across repos.

5. **TDD gate relaxation**: Markdown modules and commands are exempted from the TDD gate (imbue `tdd_bdd_gate.py`), since they contain instructional content rather than executable code. `SKILL.md` files remain gated.

### Plugin Integration Points

| Plugin | File | Trigger | Publishes To |
|--------|------|---------|-------------|
| attune | `modules/discussion-publishing.md` | Post-Phase 7 synthesis | Decisions |
| memory-palace | `modules/discussion-promotion.md` | Knowledge-librarian review | Knowledge |
| imbue | `modules/github-integration.md` | Scope-guard deferral | Deliberations |
| minister | `playbooks/github-program-rituals.md` | Weekly/monthly rituals | Decisions |

### Non-Functional Constraints

- Python 3.9.6 compatibility for all hook code (no union types, no `datetime.UTC`)
- SessionStart hook: single bounded GraphQL query, `first: 5`, 3-second timeout
- Discussion bodies capped at 2000 words; link to local files for full details
- All GraphQL templates use `-f` variables to prevent injection

## Consequences

### Positive

- War room decisions, knowledge, and scope-guard reasoning become searchable via GitHub's native UI and GraphQL
- Future sessions automatically surface relevant prior decisions (cross-session learning)
- Minister playbooks gain working Discussion commands replacing broken `gh discussion` CLI references
- Structured form templates make Discussions machine-readable
- Each plugin's integration is self-contained with no cross-plugin imports

### Negative

- Requires manual creation of Discussion categories on each repo (GitHub API limitation)
- SessionStart hook adds a GraphQL query to session startup (bounded by 3-second timeout)
- GitHub-only feature; GitLab/Bitbucket repos get no Discussion integration

### Mitigations

- Category creation documented in form template header comments
- Hook uses defensive guard chain (10 conditions) ensuring every exit emits valid JSON
- Leyline templates note "Not supported" for non-GitHub platforms

## References

- Implementation branch: `discussions-1.4.4`
- Project brief: `docs/project-brief.md`
- [GitHub Discussions GraphQL API](https://docs.github.com/en/graphql/guides/using-the-graphql-api-for-discussions)
- [Discussion Category Forms Syntax](https://docs.github.com/en/discussions/managing-discussions-for-your-community/syntax-for-discussion-category-forms)
- [Memory in the Age of AI Agents (arXiv:2512.13564)](https://arxiv.org/abs/2512.13564)
