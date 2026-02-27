# Workflow Examples

Realistic command sequences you can copy directly. Adjust paths and arguments for your project.

**See also**: [Capabilities Reference](capabilities-reference.md) | [Commands](capabilities-commands.md) | [Skills](capabilities-skills.md) | [Agents](capabilities-agents.md) | [Hooks](capabilities-hooks.md)

---

## Complete Feature Development

```bash
# 1. Brainstorm the feature
/attune:brainstorm "new API endpoint for user management"

# 2. Evaluate scope
Skill(imbue:scope-guard)
# Score: 2.3 -> Implement now

# 3. Create specification
/speckit-specify --from brainstorm.md

# 4. Generate tasks
/speckit-tasks --parallel

# 5. Implement with TDD
Skill(imbue:proof-of-work)
# Create failing tests first
/speckit-implement --phase setup
/speckit-implement --phase tests
/speckit-implement --phase core

# 6. Review code
/pensive:full-review --scope staged

# 7. Prepare PR
/prepare-pr --reviewer-scope standard
```

---

## Context Optimization

```bash
# 1. Scan for bloat
/bloat-scan --level 2 --focus code

# 2. Review findings
# High priority: 5 items, ~8,400 tokens

# 3. Create cleanup branch
git checkout -b cleanup/bloat-reduction

# 4. Execute remediation
/unbloat --approve high --backup

# 5. Verify no regressions
make test

# 6. Analyze growth trends (consolidated into bloat-scan)
/bloat-scan --level 2 --focus code

# 7. Create cleanup PR
/prepare-pr
```

---

## Quick Bug Fix

```bash
# 1. Get issue context
/sanctum:do-issue 42

# 2. Catchup on context
/catchup --focus git

# 3. Fix the bug
# ... make changes ...

# 4. Validate fix
Skill(imbue:proof-of-work)
# proof:problem-reproduced
# proof:solution-tested

# 5. Quick commit
/commit-msg --type fix --scope api

# 6. Fast PR
/prepare-pr --skip-updates --reviewer-scope lenient
```

---

## Plugin Development

```bash
# 1. Create new skill
/abstract:create-skill myplugin:new-skill --template modular

# 2. Follow TDD
Skill(abstract:skill-authoring)
# Define test scenarios
# Write acceptance criteria
# Implement skill

# 3. Validate plugin
/abstract:validate-plugin myplugin --strict

# 4. Evaluate quality
/abstract:skills-eval --plugin myplugin --threshold 80

# 5. Check hooks
/abstract:hooks-eval --plugin myplugin --security
```

---

## Knowledge Management

```bash
# 1. Review incoming knowledge
/memory-palace:review-room --status pending --batch 10

# 2. Score and curate
Skill(memory-palace:knowledge-intake)
# Apply scoring rubric
# Route to appropriate palace

# 3. Tend the garden
/garden tend

# 4. Prune stale entries
/garden prune --dry-run
/garden prune

# 5. Check garden health
/garden status
```

---

## Session Recovery

```bash
# After /clear or session restart
/catchup --depth deep

# Or focus on specific areas
/catchup --focus git --since "3 days ago"

# For git-specific recovery
/sanctum:git-catchup --since "1 week ago"
```

---

## Pre-Release Checklist

```bash
# 1. Run bloat scan
/bloat-scan --level 3 --report pre-release-audit.md

# 2. Full code review
/pensive:full-review --scope all --severity high

# 3. Update documentation
/sanctum:update-docs --check
/sanctum:update-docs --scope readme

# 4. Update tests
/sanctum:update-tests --missing --coverage

# 5. Version bump and tag
/sanctum:update-version --type minor --tag

# 6. Final PR
/prepare-pr --reviewer-scope strict
```

---

## Specification-Driven Development

```bash
# 1. Bootstrap
/speckit-startup --dir .specify/

# 2. Clarify requirements
/speckit-clarify "user authentication" --rounds 3 --technical

# 3. Create specification
/speckit-specify --from requirements.md --type full

# 4. Generate plan
/speckit-plan --from .specify/spec.md --phases --estimates

# 5. Break into tasks
/speckit-tasks --from .specify/plan.md --parallel --granularity fine

# 6. Execute tasks
/speckit-implement --phase setup
/speckit-implement --continue

# 7. Verify consistency
/speckit-analyze --strict
```

---

**See also**: [Commands](capabilities-commands.md) | [Skills](capabilities-skills.md) | [Agents](capabilities-agents.md) | [Hooks](capabilities-hooks.md)
