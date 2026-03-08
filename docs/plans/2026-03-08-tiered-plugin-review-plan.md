# Tiered Plugin Review Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use
> superpowers:executing-plans to implement this plan
> task-by-task.

**Goal:** Add tiered review orchestration to `/plugin-review`
(branch/pr/release), dependency-aware scoping, and integration
with `/update-plugins`.

**Architecture:** The existing `/plugin-review` command
(abstract) becomes a tiered skill that detects affected
plugins from the git diff, resolves related plugins via a
static dependency map, and dispatches the appropriate depth
of quality checks. `/update-plugins` (sanctum) calls it as
Phase 2.

**Tech Stack:** Markdown skills with modular loading, Python
script for dependency map generation, JSON for dependency
data.

---

### Task 1: Generate Plugin Dependency Map

**Files:**
- Create: `scripts/generate_dependency_map.py`
- Create: `docs/plugin-dependencies.json`

**Step 1: Write the test**

Create `tests/scripts/test_generate_dependency_map.py`:

```python
"""Tests for plugin dependency map generator."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path("scripts/generate_dependency_map.py")
REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestDependencyMapGenerator:
    """Test dependency map generation."""

    def test_script_runs_successfully(self) -> None:
        """Given the script exists, when run, then exit 0."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--stdout"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, result.stderr

    def test_output_is_valid_json(self) -> None:
        """Given the script runs, when output captured,
        then it is valid JSON."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--stdout"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        data = json.loads(result.stdout)
        assert "version" in data
        assert "dependencies" in data
        assert "reverse_index" in data

    def test_abstract_is_universal_dependency(self) -> None:
        """Given abstract provides Make includes to all,
        when map generated, then abstract has wildcard."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--stdout"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        data = json.loads(result.stdout)
        assert "abstract" in data["dependencies"]
        assert data["dependencies"]["abstract"]["dependents"] == ["*"]

    def test_conjure_depends_on_leyline(self) -> None:
        """Given conjure optionally imports leyline,
        when map generated, then reverse_index shows it."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--stdout"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        data = json.loads(result.stdout)
        assert "leyline" in data["reverse_index"].get("conjure", [])

    def test_all_plugins_in_reverse_index(self) -> None:
        """Given 17 plugins exist, when map generated,
        then all non-abstract plugins appear in reverse_index."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--stdout"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        data = json.loads(result.stdout)
        # abstract itself is a dependency, not a dependent
        assert len(data["reverse_index"]) >= 16
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/alex.thola/claude-night-market && uv run pytest tests/scripts/test_generate_dependency_map.py -v --no-cov --tb=short`
Expected: FAIL (script doesn't exist)

**Step 3: Write the script**

Create `scripts/generate_dependency_map.py`:

```python
#!/usr/bin/env python3
"""Generate plugin dependency map by scanning Makefiles and pyproject.toml.

Scans:
- Makefile `-include` directives (build-time deps)
- pyproject.toml dependencies (runtime deps)
- Python imports in src/ and scripts/ (runtime coupling)

Output: JSON to stdout (--stdout) or docs/plugin-dependencies.json
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path


def find_plugins(plugins_dir: Path) -> list[str]:
    """Find all plugin directories."""
    plugins = []
    for d in sorted(plugins_dir.iterdir()):
        if d.is_dir() and (d / ".claude-plugin" / "plugin.json").exists():
            plugins.append(d.name)
    return plugins


def scan_makefile_deps(plugin_dir: Path, all_plugins: list[str]) -> list[dict]:
    """Scan Makefile for -include directives referencing other plugins."""
    makefile = plugin_dir / "Makefile"
    if not makefile.exists():
        return []

    deps = []
    content = makefile.read_text(encoding="utf-8")
    for line in content.splitlines():
        match = re.match(r'^-?include\s+.*\.\./(\w[\w-]*)/(.+)', line)
        if not match:
            # Also match variable-based includes
            match = re.match(
                r'^\s*(\w+_DIR)\s*:=\s*\.\./(\w[\w-]*)', line,
            )
            if match:
                dep_plugin = match.group(2)
                if dep_plugin in all_plugins:
                    deps.append({
                        "plugin": dep_plugin,
                        "type": "build",
                        "reason": f"Makefile include ({match.group(1)})",
                    })
                continue
            continue
        dep_plugin = match.group(1)
        if dep_plugin in all_plugins:
            deps.append({
                "plugin": dep_plugin,
                "type": "build",
                "reason": f"Makefile include ({match.group(2)})",
            })
    return deps


def scan_pyproject_deps(
    plugin_dir: Path, all_plugins: list[str],
) -> list[dict]:
    """Scan pyproject.toml for inter-plugin dependencies."""
    pyproject = plugin_dir / "pyproject.toml"
    if not pyproject.exists():
        return []

    deps = []
    content = pyproject.read_text(encoding="utf-8")

    # Normalize plugin names for matching (hyphens vs underscores)
    plugin_names = {}
    for p in all_plugins:
        plugin_names[p] = p
        plugin_names[p.replace("-", "_")] = p
        plugin_names[p.replace("-", "")] = p

    for line in content.splitlines():
        line_stripped = line.strip().strip('"').strip("'").strip(",")
        for norm_name, orig_name in plugin_names.items():
            if (
                norm_name == plugin_dir.name
                or norm_name == plugin_dir.name.replace("-", "_")
            ):
                continue
            if re.match(rf'^{re.escape(norm_name)}(\s*[><=!]|$)', line_stripped):
                deps.append({
                    "plugin": orig_name,
                    "type": "runtime",
                    "reason": "pyproject.toml dependency",
                })
                break
    return deps


def scan_python_imports(
    plugin_dir: Path,
    plugin_name: str,
    all_plugins: list[str],
) -> list[dict]:
    """Scan Python files for cross-plugin imports."""
    deps = []
    seen = set()

    # Normalize for import matching
    import_names = {}
    for p in all_plugins:
        import_names[p.replace("-", "_")] = p

    src_dirs = [plugin_dir / "src", plugin_dir / "scripts"]
    for src_dir in src_dirs:
        if not src_dir.exists():
            continue
        for py_file in src_dir.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for line in content.splitlines():
                for imp_name, orig_name in import_names.items():
                    if orig_name == plugin_name:
                        continue
                    if orig_name in seen:
                        continue
                    pattern = rf'(?:from|import)\s+{re.escape(imp_name)}\b'
                    if re.search(pattern, line):
                        seen.add(orig_name)
                        deps.append({
                            "plugin": orig_name,
                            "type": "runtime",
                            "reason": f"Python import in {py_file.name}",
                        })
    return deps


def generate_map(plugins_dir: Path) -> dict:
    """Generate the full dependency map."""
    all_plugins = find_plugins(plugins_dir)

    dependencies = {}
    reverse_index = {}

    # Initialize reverse index
    for plugin in all_plugins:
        reverse_index[plugin] = []

    # Scan each plugin
    for plugin in all_plugins:
        plugin_dir = plugins_dir / plugin
        all_deps = []
        all_deps.extend(scan_makefile_deps(plugin_dir, all_plugins))
        all_deps.extend(scan_pyproject_deps(plugin_dir, all_plugins))
        all_deps.extend(
            scan_python_imports(plugin_dir, plugin, all_plugins),
        )

        # Deduplicate
        seen_plugins = set()
        for dep in all_deps:
            dep_name = dep["plugin"]
            if dep_name in seen_plugins:
                continue
            seen_plugins.add(dep_name)

            # Add to reverse index
            if dep_name not in reverse_index[plugin]:
                reverse_index[plugin].append(dep_name)

    # Build forward dependencies (which plugins are depended on)
    for plugin in all_plugins:
        # Count how many plugins depend on this one
        dependents = [
            p for p, deps in reverse_index.items()
            if plugin in deps and p != plugin
        ]
        if dependents:
            dep_type = "build"
            reason = "Shared Make includes"
            # Check if all plugins depend on it
            non_self = [p for p in all_plugins if p != plugin]
            if set(dependents) == set(non_self):
                dependents_val = ["*"]
            else:
                dependents_val = sorted(dependents)
                # Infer type from first dependent's reason
                for p in dependents:
                    for dep_name in reverse_index[p]:
                        if dep_name == plugin:
                            break
                dep_type = "build"
                reason = "Shared infrastructure"
            dependencies[plugin] = {
                "dependents": dependents_val,
                "type": dep_type,
                "reason": reason,
            }

    # Remove self-references from reverse index
    for plugin in all_plugins:
        reverse_index[plugin] = [
            d for d in reverse_index[plugin] if d != plugin
        ]
    # Remove plugins with no dependencies from reverse index
    reverse_index = {
        k: sorted(v) for k, v in reverse_index.items() if v
    }

    return {
        "version": "1.0.0",
        "generated": datetime.date.today().isoformat(),
        "dependencies": dependencies,
        "reverse_index": reverse_index,
    }


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(
        description="Generate plugin dependency map",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print to stdout instead of writing file",
    )
    parser.add_argument(
        "--output",
        default="docs/plugin-dependencies.json",
        help="Output file path (default: docs/plugin-dependencies.json)",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    plugins_dir = repo_root / "plugins"

    if not plugins_dir.exists():
        print("Error: plugins/ directory not found", file=sys.stderr)
        sys.exit(1)

    dep_map = generate_map(plugins_dir)

    output = json.dumps(dep_map, indent=2, sort_keys=False) + "\n"

    if args.stdout:
        print(output, end="")
    else:
        out_path = repo_root / args.output
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output, encoding="utf-8")
        print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/alex.thola/claude-night-market && uv run pytest tests/scripts/test_generate_dependency_map.py -v --no-cov --tb=short`
Expected: PASS (all 5 tests)

**Step 5: Generate the initial map**

Run: `cd /Users/alex.thola/claude-night-market && python3 scripts/generate_dependency_map.py`
Expected: `docs/plugin-dependencies.json` created

**Step 6: Commit**

```bash
git add scripts/generate_dependency_map.py \
  tests/scripts/test_generate_dependency_map.py \
  docs/plugin-dependencies.json
git commit -m "feat: add plugin dependency map generator"
```

---

### Task 2: Create Plugin Review Skill (SKILL.md)

**Files:**
- Create: `plugins/abstract/skills/plugin-review/SKILL.md`

**Step 1: Create the skill directory and SKILL.md**

```markdown
---
name: plugin-review
description: "Tiered plugin quality review with dependency-aware
  scoping. Use when: reviewing plugin changes, preparing PRs,
  pre-release validation. Do not use when: single skill analysis
  (use /analyze-skill), creating new skills (use /create-skill)."
category: plugin-management
tags:
- review
- quality
- validation
- testing
- architecture
dependencies:
- skills-eval
- hooks-eval
- rules-eval
tools:
- validate_plugin.py
- skill_analyzer.py
- generate_dependency_map.py
progressive_loading: true
---

# Plugin Review

Tiered quality review of plugins with dependency-aware scoping.

## Tiers

| Tier | Trigger | Scope | Depth | Duration |
|------|---------|-------|-------|----------|
| branch | Default | Affected + related | Quick gates | ~2 min |
| pr | Before merge | Affected + related | Standard | ~5 min |
| release | Before version bump | All 17 plugins | Full | ~15 min |

## Orchestration

1. **Detect scope**: parse `--tier` flag, find affected
   plugins from git diff, resolve related plugins from
   `docs/plugin-dependencies.json`
2. **Plan**: build check matrix (tier x plugin x role)
3. **Execute**: run checks per tier definition
4. **Report**: per-plugin table, aggregate verdict

## Scope Detection

Affected plugins: `git diff main --name-only` filtered to
`plugins/*/`.

Related plugins: load `docs/plugin-dependencies.json`,
look up each affected plugin's reverse index to find
dependents. Mark as "related" (lighter checks).

If `--tier release` or no git diff available, scope to
all plugins.

## Module Loading

- **Always**: this SKILL.md (orchestration logic)
- **branch tier**: load `modules/tier-branch.md`
- **pr tier**: load `modules/tier-branch.md` then
  `modules/tier-pr.md`
- **release tier**: load all tier modules plus
  `modules/tier-release.md`
- **When resolving deps**: load
  `modules/dependency-detection.md`

## Verdict

| Result | Meaning |
|--------|---------|
| PASS | All checks green |
| PASS-WITH-WARNINGS | Non-blocking issues |
| FAIL | Blocking issues found |

## Output Format

```
Plugin Review (<tier> tier)
Affected: <list>
Related:  <list> (<reason>)

Plugin          test  lint  type  reg   verdict
<name>          PASS  PASS  PASS  PASS  PASS
...

Verdict: <PASS|WARN|FAIL> (N/N plugins healthy)
```

PR and release tiers add scorecard sections.
```

**Step 2: Verify skill is discoverable**

Run: `ls plugins/abstract/skills/plugin-review/SKILL.md`
Expected: file exists

**Step 3: Commit**

```bash
git add plugins/abstract/skills/plugin-review/SKILL.md
git commit -m "feat(abstract): add plugin-review skill with tier orchestration"
```

---

### Task 3: Create Tier Module -- Branch

**Files:**
- Create: `plugins/abstract/skills/plugin-review/modules/tier-branch.md`

**Step 1: Write the module**

```markdown
# Branch Tier Checks

The branch tier runs quick quality gates on affected and
related plugins. Designed for fast feedback during
development.

## Checks for Affected Plugins

Run these sequentially for each affected plugin:

### 1. Registration Audit

```bash
python3 plugins/sanctum/scripts/update_plugin_registrations.py \
  <plugin-name> --dry-run
```

Report any missing or stale registrations.

### 2. Test Gate

```bash
cd plugins/<plugin> && make test
```

Capture pass/fail and test count. If tests fail, mark
plugin as FAIL.

### 3. Lint Gate

```bash
cd plugins/<plugin> && make lint
```

Capture pass/fail. If lint fails, mark as WARNING (not
blocking at branch tier).

### 4. Typecheck Gate

```bash
cd plugins/<plugin> && make typecheck
```

Capture pass/fail. If typecheck fails, mark as WARNING.

### 5. Diff Analysis

Run `git diff main -- plugins/<plugin>/` to identify:
- New files (commands, skills, hooks, agents)
- Deleted files
- Modified production code vs test-only changes

Flag high-risk patterns:
- Hook changes (security surface)
- `__init__.py` export changes (API surface)
- pyproject.toml dependency changes

## Checks for Related Plugins

Run a lighter subset:

### 1. Registration Audit

Same as affected plugins.

### 2. Test Gate

```bash
cd plugins/<plugin> && make test
```

Tests must pass. This catches side-effect breakage from
dependency changes.

## Result Table

Build a table with columns: plugin, test, lint, type, reg,
verdict. Use `--` for skipped checks on related plugins.

## Verdict Rules

- Any test FAIL on affected or related: overall FAIL
- Any lint/type FAIL on affected: overall PASS-WITH-WARNINGS
- All green: PASS
```

**Step 2: Commit**

```bash
git add plugins/abstract/skills/plugin-review/modules/tier-branch.md
git commit -m "feat(abstract): add branch tier module for plugin-review"
```

---

### Task 4: Create Tier Module -- PR

**Files:**
- Create: `plugins/abstract/skills/plugin-review/modules/tier-pr.md`

**Step 1: Write the module**

```markdown
# PR Tier Checks

The PR tier adds quality scoring on top of branch tier
gates. Runs before merge.

## Additional Checks for Affected Plugins

After all branch tier checks pass, run these:

### 1. Skills Evaluation

Invoke `Skill(abstract:skills-eval)` for each affected
plugin. Capture:
- Per-skill quality scores
- Token efficiency ratings
- Compliance status

Report any skill scoring below 70 (MINIMUM_QUALITY_THRESHOLD).

### 2. Hooks Evaluation

If the plugin has hooks that changed in the diff:

Invoke `Skill(abstract:hooks-eval)` targeting only changed
hook files. Capture:
- Security findings
- Performance concerns
- Compliance status

### 3. Test Review

Invoke `Skill(pensive:test-review)` for each affected plugin.
Capture:
- Coverage percentage
- Anti-pattern findings
- Missing edge cases

### 4. Quick Bloat Scan

Invoke `Skill(conserve:bloat-scan)` at Tier 1 (quick) for
each affected plugin. Capture:
- Dead code candidates
- Duplicate content
- Stale files

### 5. Rules Evaluation

If `.claude/rules/` files changed in the diff:

Invoke `Skill(abstract:rules-eval)`. Capture:
- YAML validity
- Pattern specificity
- Content quality

## Parallel Execution

Group affected plugins into 2-3 clusters and dispatch
agents in parallel. Each agent runs the full PR check
suite on its assigned plugins.

## Scorecard Output

Add a scorecard section after the branch tier table:

```
Scorecard (PR tier)

Plugin          skills  hooks  tests  bloat  grade
sanctum         88/100  92/100 93%    90/100 A-
memory-palace   85/100  --     89%    82/100 B+

Top 5 Remediation Actions:
1. [sanctum] skills/commit-messages: missing trigger phrases
2. [memory-palace] hooks/research_interceptor.py: no timeout
...
```

## Verdict Rules

- Any branch-tier FAIL: overall FAIL
- Any skill score below 50: overall FAIL
- Any security finding (HIGH): overall FAIL
- All scores above 70: PASS
- Otherwise: PASS-WITH-WARNINGS with details
```

**Step 2: Commit**

```bash
git add plugins/abstract/skills/plugin-review/modules/tier-pr.md
git commit -m "feat(abstract): add PR tier module for plugin-review"
```

---

### Task 5: Create Tier Module -- Release

**Files:**
- Create: `plugins/abstract/skills/plugin-review/modules/tier-release.md`

**Step 1: Write the module**

```markdown
# Release Tier Checks

The release tier runs a full ecosystem audit across all 17
plugins. Requires plan mode for parallel agent dispatch.

## Scope

All 17 plugins, regardless of git diff. This is the
pre-release validation gate.

## Additional Checks (Beyond PR Tier)

### 1. Architecture Review

Invoke `Skill(pensive:architecture-review)` to assess:
- ADR compliance across all plugins
- Cross-plugin coupling analysis
- Module boundary violations
- Design pattern adherence

### 2. Unified Review

Invoke `Skill(pensive:unified-review)` for multi-domain
orchestration covering API, architecture, test, and code
quality dimensions.

### 3. Deep Bloat Scan

Invoke `Skill(conserve:bloat-scan)` at Tier 2-3 (deep) for
full dead code analysis, cross-file duplication detection,
and dependency audit.

### 4. Token Efficiency Analysis

For each plugin, calculate:
- Total skill description budget usage
- Per-skill token estimates
- Progressive loading compliance
- Module size distribution

Flag any plugin exceeding its proportional token budget
allocation.

### 5. Meta-Evaluation

Run `python3 plugins/sanctum/scripts/meta_evaluation.py`
to validate that evaluation-related skills (skills-eval,
hooks-eval, rules-eval) meet their own quality standards.

### 6. Cross-Plugin Dependency Validation

Regenerate the dependency map and compare with the committed
version:

```bash
python3 scripts/generate_dependency_map.py --stdout | \
  diff - docs/plugin-dependencies.json
```

Flag any drift between actual and documented dependencies.

## Agent Dispatch Plan

Requires plan mode (4+ agents rule). Suggested grouping:

| Agent | Plugins | Focus |
|-------|---------|-------|
| 1 | abstract, leyline | Foundation layer |
| 2 | sanctum, imbue, conserve | Core infrastructure |
| 3 | attune, conjure, hookify | Workflow plugins |
| 4 | pensive, memory-palace, minister | Domain specialists |
| 5 | parseltongue, egregore, spec-kit | Language/pipeline |
| 6 | scribe, scry, archetypes | Media/docs/patterns |

Each agent runs full PR-tier checks on its plugins plus
the release-specific checks.

## Full Ecosystem Report

```
Plugin Review (release tier) - v1.5.6
Date: 2026-03-08
Plugins: 17/17

ECOSYSTEM HEALTH
Plugin          test  lint  type  skills hooks  bloat  grade
abstract        PASS  PASS  PASS  92     88     90     A
attune          PASS  PASS  PASS  85     --     82     B+
conjure         PASS  PASS  PASS  88     85     87     A-
...

ARCHITECTURE
ADR compliance: 7/7
Coupling score: 0.06
Boundary violations: 0

TOKEN BUDGET
Used: 15,200 / 17,000 chars (89.4%)
Largest: attune (3,920 chars, 23.1%)

DEPENDENCY MAP
Status: current (no drift)

Verdict: PASS (17/17 plugins healthy)
```

## Verdict Rules

- Any test FAIL: overall FAIL
- Any security finding (HIGH): overall FAIL
- ADR violation without justification: overall FAIL
- Coupling score > 0.7: FAIL
- All plugins grade B or above: PASS
- Otherwise: PASS-WITH-WARNINGS
```

**Step 2: Commit**

```bash
git add plugins/abstract/skills/plugin-review/modules/tier-release.md
git commit -m "feat(abstract): add release tier module for plugin-review"
```

---

### Task 6: Create Dependency Detection Module

**Files:**
- Create: `plugins/abstract/skills/plugin-review/modules/dependency-detection.md`

**Step 1: Write the module**

```markdown
# Dependency Detection

How to resolve affected and related plugins for scoped
review.

## Affected Plugins

Detect from git diff against the base branch:

```bash
git diff main --name-only | \
  grep '^plugins/' | \
  sed 's|^plugins/\([^/]*\)/.*|\1|' | \
  sort -u
```

If no diff available (detached HEAD, no main branch),
fall back to all plugins.

## Related Plugins

Load `docs/plugin-dependencies.json` and for each affected
plugin, look up who depends on it:

1. Read the `dependencies` section to find the affected
   plugin
2. If `dependents` is `["*"]`, ALL other plugins are related
3. Otherwise, `dependents` lists the specific related plugins

Example: if `abstract` is affected and has
`dependents: ["*"]`, then all 16 other plugins are related.

If `leyline` is affected and has `dependents: ["conjure"]`,
then only conjure is related.

## Deduplication

A plugin that is both affected (has direct changes) AND
related (depends on another changed plugin) is treated as
affected. The "affected" role always wins.

## Special Cases

- **Root-level changes** (pyproject.toml, Makefile, scripts/):
  These affect the workspace, not individual plugins.
  At branch tier, skip. At pr/release tier, flag for
  manual review.

- **No plugins changed**: If the diff has no plugin changes,
  report "No plugin changes detected" and exit with PASS.

- **New plugin**: If a plugin directory exists on disk but
  is not in `plugin-dependencies.json`, flag it and suggest
  running `scripts/generate_dependency_map.py` to update.
```

**Step 2: Commit**

```bash
git add plugins/abstract/skills/plugin-review/modules/dependency-detection.md
git commit -m "feat(abstract): add dependency detection module for plugin-review"
```

---

### Task 7: Update /plugin-review Command

**Files:**
- Modify: `plugins/abstract/commands/plugin-review.md:1-5`
  (frontmatter) and add tier documentation

**Step 1: Update the command frontmatter and usage section**

Replace the frontmatter and Usage section in
`plugins/abstract/commands/plugin-review.md` to add
`--tier` flag:

Old frontmatter (lines 1-5):
```yaml
---
name: plugin-review
description: Rigorous review of plugin architecture quality. Orchestrates multiple evaluation tools to provide a unified health report covering skills, commands, hooks, agents, token efficiency, and bloat detection.
usage: /plugin-review [plugin-path] [--focus skills|hooks|bloat|tokens|all] [--format summary|detailed|json]
---
```

New frontmatter:
```yaml
---
name: plugin-review
description: "Tiered plugin quality review: branch (quick gates),
  pr (quality scoring), release (full ecosystem audit).
  Detects affected plugins from git diff and reviews
  related plugins for side effects."
usage: "/plugin-review [plugin-name...] [--tier branch|pr|release]
  [--focus skills|hooks|bloat|tokens|all]
  [--format summary|detailed|json] [--plan]"
---
```

Add a new "Tiers" section after the "Usage" section
documenting the three tiers and their checks (reference
the tier modules).

Preserve all existing content below (What It Reviews,
Output Format, Quality Levels, CI/CD Integration,
Related Commands sections).

**Step 2: Verify the command is still registered**

Run: `python3 plugins/sanctum/scripts/update_plugin_registrations.py abstract --dry-run`
Expected: No discrepancies

**Step 3: Commit**

```bash
git add plugins/abstract/commands/plugin-review.md
git commit -m "feat(abstract): add tier flag to /plugin-review command"
```

---

### Task 8: Update /update-plugins Command

**Files:**
- Modify: `plugins/sanctum/commands/update-plugins.md:24-27`

**Step 1: Update Phase 2 description**

Replace lines 24-27 in
`plugins/sanctum/commands/update-plugins.md`:

Old:
```markdown
### Phase 2-4 (On-Demand Modules)
- See `modules/phase2-performance.md` for performance and improvement analysis
- See `modules/phase3-meta-eval.md` for recursive quality validation
- See `modules/phase4-queue.md` for knowledge queue promotion checks
```

New:
```markdown
### Phase 2: Plugin Quality Review
Triggers `/plugin-review --tier branch` on affected plugins.
Runs quick quality gates (test, lint, typecheck, registration)
on changed plugins and side-effect checks on related plugins.

### Phase 3-4 (On-Demand Modules)
- See `modules/phase3-meta-eval.md` for recursive quality
  validation
- See `modules/phase4-queue.md` for knowledge queue promotion
  checks
```

Also add to the Integration section:
```markdown
- `/plugin-review` - Tiered quality review (invoked as Phase 2)
```

**Step 2: Commit**

```bash
git add plugins/sanctum/commands/update-plugins.md
git commit -m "feat(sanctum): integrate /plugin-review as Phase 2 of /update-plugins"
```

---

### Task 9: Register Plugin Review Skill in plugin.json

**Files:**
- Modify: `plugins/abstract/.claude-plugin/plugin.json`

**Step 1: Add the skill to plugin.json**

The new `skills/plugin-review` directory needs to be
registered. Add `"./skills/plugin-review"` to the `skills`
array in `plugins/abstract/.claude-plugin/plugin.json`,
maintaining alphabetical order.

**Step 2: Verify registration**

Run: `python3 plugins/sanctum/scripts/update_plugin_registrations.py abstract --dry-run`
Expected: No discrepancies (or the script detects it's
missing and `--fix` adds it)

**Step 3: Commit**

```bash
git add plugins/abstract/.claude-plugin/plugin.json
git commit -m "feat(abstract): register plugin-review skill in plugin.json"
```

---

### Task 10: End-to-End Validation

**Step 1: Run the dependency map generator**

Run: `python3 scripts/generate_dependency_map.py`
Verify: `docs/plugin-dependencies.json` exists and has
correct structure

**Step 2: Run /update-plugins to verify integration**

Run: `python3 plugins/sanctum/scripts/update_plugin_registrations.py --dry-run`
Expected: All 17 plugins clean

**Step 3: Verify skill is loadable**

Check: `plugins/abstract/skills/plugin-review/SKILL.md`
has valid YAML frontmatter and modules directory with 4
files.

**Step 4: Commit design and plan docs**

```bash
git add docs/plans/2026-03-08-tiered-plugin-review-design.md \
  docs/plans/2026-03-08-tiered-plugin-review-plan.md
git commit -m "docs: add tiered plugin review design and plan"
```
