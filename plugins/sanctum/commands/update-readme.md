---
name: update-readme
description: Update README with git context and exemplar research
usage: /update-readme
---

# Update README Content

<identification>
triggers: update readme, readme update, documentation update

use_when:
- README needs updates after code changes
- Consolidating documentation with recent work
</identification>

To edit the README, load the required skills in order:

1. Run `Skill(sanctum:git-workspace-review)` to capture the change context and complete its `TodoWrite` items.
2. Run `Skill(sanctum:update-readme)` and follow its checklist (context, exemplar research, content consolidation, verification).

## Workflow
- Use notes from the preflight to understand recent changes that affect the README.
- Research language-aware README exemplars via web search for the project's primary language.
- Consolidate README sections with internal documentation links and reproducible evidence.
- Apply project writing guidelines and verify that all links and code examples work.
- Run `Skill(scribe:slop-detector)` on the updated README to detect AI-generated content markers.
- Apply `scribe:doc-generator` principles if slop score exceeds threshold.

## Manual Execution
If a skill cannot be loaded, follow these steps:
- Manually gather the Git context (`pwd`, `git status -sb`, `git diff --stat`).
- Review the current README structure and update sections based on recent changes.
- Verify all links and examples before finalizing.
- Check for AI slop using scribe guidelines: avoid "leverage", "comprehensive", "cutting-edge", excessive em dashes, and marketing language.

## See Also
- `/slop-scan` - Direct AI slop detection (scribe plugin)
- `/doc-polish` - Interactive documentation cleanup (scribe plugin)
- `/update-docs` - General documentation updates
