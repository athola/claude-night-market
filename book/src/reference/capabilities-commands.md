# Command Reference — Core Plugins

Flag and option documentation for core plugin commands (abstract, attune, conserve, imbue, sanctum).

**Extended plugins**: [Memory Palace, Pensive, Parseltongue, Spec-Kit, Scribe, Scry, Hookify, Leyline](capabilities-commands-extended.md)

**See also**: [Capabilities Reference](capabilities-reference.md) | [Skills](capabilities-skills.md) | [Agents](capabilities-agents.md) | [Hooks](capabilities-hooks.md) | [Workflows](capabilities-workflows.md)

---

## Command Syntax

```bash
/<plugin>:<command-name> [--flags] [positional-args]
```

**Common Flag Patterns:**
| Flag Pattern | Description | Example |
|--------------|-------------|---------|
| `--verbose` | Enable detailed output | `/bloat-scan --verbose` |
| `--dry-run` | Preview without executing | `/unbloat --dry-run` |
| `--force` | Skip confirmation prompts | `/attune:init --force` |
| `--report FILE` | Output to file | `/bloat-scan --report audit.md` |
| `--level N` | Set intensity/depth | `/bloat-scan --level 3` |
| `--skip-X` | Skip specific phase | `/prepare-pr --skip-updates` |

---

## Abstract Plugin

### `/abstract:validate-plugin`
Validate plugin structure against ecosystem conventions.

```bash
# Usage
/abstract:validate-plugin [plugin-name] [--strict] [--fix]

# Options
--strict       Fail on warnings (not just errors)
--fix          Auto-fix correctable issues
--report FILE  Output validation report

# Examples
/abstract:validate-plugin sanctum
/abstract:validate-plugin --strict conserve
/abstract:validate-plugin memory-palace --fix
```

### `/abstract:create-skill`
Scaffold a new skill with proper frontmatter and structure.

```bash
# Usage
/abstract:create-skill <plugin>:<skill-name> [--template basic|modular] [--category]

# Options
--template     Skill template type (basic or modular with modules/)
--category     Skill category for classification
--interactive  Guided creation flow

# Examples
/abstract:create-skill pensive:shell-review --template modular
/abstract:create-skill imbue:new-methodology --category workflow-methodology
```

### `/abstract:create-command`
Scaffold a new command with hooks and documentation.

```bash
# Usage
/abstract:create-command <plugin>:<command-name> [--hooks] [--extends]

# Options
--hooks        Include lifecycle hook templates
--extends      Base command or skill to extend
--aliases      Comma-separated command aliases

# Examples
/abstract:create-command sanctum:new-workflow --hooks
/abstract:create-command conserve:deep-clean --extends "conserve:bloat-scan"
```

### `/abstract:create-hook`
Scaffold a new hook with security-first patterns.

```bash
# Usage
/abstract:create-hook <plugin>:<hook-name> [--type] [--lang]

# Options
--type     Hook event type (PreToolUse|PostToolUse|SessionStart|Stop|UserPromptSubmit)
--lang     Implementation language (bash|python)
--matcher  Tool matcher pattern

# Examples
/abstract:create-hook memory-palace:cache-check --type PreToolUse --lang python
/abstract:create-hook sanctum:commit-validator --type PreToolUse --matcher "Bash"
```

### `/abstract:analyze-skill`
Analyze skill complexity and optimization opportunities.

```bash
# Usage
/abstract:analyze-skill <plugin>:<skill-name> [--metrics] [--suggest]

# Options
--metrics    Show detailed token/complexity metrics
--suggest    Generate optimization suggestions
--compare    Compare against skill baselines

# Examples
/abstract:analyze-skill imbue:proof-of-work --metrics
/abstract:analyze-skill sanctum:pr-prep --suggest
```

### `/abstract:make-dogfood`
Update Makefile demonstration targets to reflect current features.

```bash
# Usage
/abstract:make-dogfood [--check] [--update]

# Options
--check     Verify Makefile is current (exit 1 if stale)
--update    Apply updates to Makefile
--dry-run   Show what would change

# Examples
/abstract:make-dogfood --check
/abstract:make-dogfood --update
```

### `/abstract:skills-eval`
Evaluate skill quality across the ecosystem.

```bash
# Usage
/abstract:skills-eval [--plugin PLUGIN] [--threshold SCORE]

# Options
--plugin     Limit to specific plugin
--threshold  Minimum quality score (default: 70)
--output     Output format (table|json|markdown)

# Examples
/abstract:skills-eval --plugin sanctum
/abstract:skills-eval --threshold 80 --output markdown
```

### `/abstract:hooks-eval`
Evaluate hook security and performance.

```bash
# Usage
/abstract:hooks-eval [--plugin PLUGIN] [--security]

# Options
--plugin    Limit to specific plugin
--security  Focus on security patterns
--perf      Focus on performance impact

# Examples
/abstract:hooks-eval --security
/abstract:hooks-eval --plugin memory-palace --perf
```

### `/abstract:evaluate-skill`
Evaluate skill execution quality.

```bash
# Usage
/abstract:evaluate-skill <plugin>:<skill-name> [--metrics] [--suggestions]

# Options
--metrics      Show detailed execution metrics
--suggestions  Generate improvement suggestions
--compare      Compare against baseline metrics

# Examples
/abstract:evaluate-skill imbue:proof-of-work --metrics
/abstract:evaluate-skill sanctum:pr-prep --suggestions
```

---

## Attune Plugin

### `/attune:init`
Initialize project with complete development infrastructure.

```bash
# Usage
/attune:init [--lang LANGUAGE] [--name NAME] [--author AUTHOR]

# Options
--lang LANGUAGE         Project language: python|rust|typescript|go
--name NAME             Project name (default: directory name)
--author AUTHOR         Author name
--email EMAIL           Author email
--python-version VER    Python version (default: 3.10)
--description TEXT      Project description
--path PATH             Project path (default: .)
--force                 Overwrite existing files without prompting
--no-git                Skip git initialization

# Examples
/attune:init --lang python --name my-cli
/attune:init --lang rust --author "Your Name" --force
```

### `/attune:brainstorm`
Brainstorm project ideas using Socratic questioning.

```bash
# Usage
/attune:brainstorm [TOPIC] [--output FILE]

# Options
--output FILE    Save brainstorm results to file
--rounds N       Number of question rounds (default: 5)
--focus AREA     Focus area: features|architecture|ux|technical

# Examples
/attune:brainstorm "CLI tool for data processing"
/attune:brainstorm --focus architecture --rounds 3
```

### `/attune:blueprint`
Plan architecture and break down tasks.

```bash
# Usage
/attune:blueprint [--from BRAINSTORM] [--output FILE]

# Options
--from FILE      Use brainstorm results as input
--output FILE    Save plan to file
--depth LEVEL    Planning depth: high|detailed|exhaustive
--include        Include specific aspects: tests|ci|docs

# Examples
/attune:blueprint --from brainstorm.md --depth detailed
/attune:blueprint --include tests,ci
```

### `/attune:specify`
Create detailed specifications from brainstorm or plan.

```bash
# Usage
/attune:specify [--from FILE] [--type TYPE]

# Options
--from FILE    Input file (brainstorm or plan)
--type TYPE    Spec type: technical|functional|api|data-model
--output DIR   Output directory for specs

# Examples
/attune:specify --from plan.md --type technical
/attune:specify --type api --output .specify/
```

### `/attune:execute`
Execute implementation tasks systematically.

```bash
# Usage
/attune:execute [--plan FILE] [--phase PHASE] [--task ID]

# Options
--plan FILE     Task plan file (default: .specify/tasks.md)
--phase PHASE   Execute specific phase: setup|tests|core|integration|polish
--task ID       Execute specific task by ID
--parallel      Enable parallel execution where marked [P]
--continue      Resume from last checkpoint

# Examples
/attune:execute --plan tasks.md --phase setup
/attune:execute --task T1.2 --parallel
```

### `/attune:validate`
Validate project structure against best practices.

```bash
# Usage
/attune:validate [--strict] [--fix]

# Options
--strict    Fail on warnings
--fix       Auto-fix correctable issues
--config    Path to custom validation config

# Examples
/attune:validate --strict
/attune:validate --fix
```

### `/attune:upgrade-project`
Add or update configurations in existing project.

```bash
# Usage
/attune:upgrade-project [--component COMPONENT] [--force]

# Options
--component    Specific component: makefile|precommit|workflows|gitignore
--force        Overwrite existing without prompting
--diff         Show diff before applying

# Examples
/attune:upgrade-project --component makefile
/attune:upgrade-project --component workflows --force
```

---

## Conserve Plugin

### `/conserve:bloat-scan`
Progressive bloat detection for dead code and duplication.

```bash
# Usage
/bloat-scan [--level 1|2|3] [--focus TYPE] [--report FILE] [--dry-run]

# Options
--level 1|2|3      Scan tier: 1=quick, 2=targeted, 3=deep audit
--focus TYPE       Focus area: code|docs|deps|all (default: all)
--report FILE      Save report to file
--dry-run          Preview findings without taking action
--exclude PATTERN  Additional exclude patterns

# Scan Tiers
# Tier 1 (2-5 min): Large files, stale files, commented code, old TODOs
# Tier 2 (10-20 min): Dead code, duplicate patterns, import bloat
# Tier 3 (30-60 min): All above + cyclomatic complexity, dependency graphs

# Examples
/bloat-scan                           # Quick Tier 1 scan
/bloat-scan --level 2 --focus code    # Targeted code analysis
/bloat-scan --level 3 --report Q1-audit.md  # Deep audit with report
```

### `/conserve:unbloat`
Safe bloat remediation with interactive approval.

```bash
# Usage
/unbloat [--approve LEVEL] [--dry-run] [--backup]

# Options
--approve LEVEL    Auto-approve level: high|medium|low|all
--dry-run          Show what would be removed
--backup           Create backup branch before changes
--interactive      Prompt for each item (default)

# Examples
/unbloat --dry-run                    # Preview all removals
/unbloat --approve high --backup      # Auto-approve high priority, backup first
/unbloat --interactive                # Approve each item manually
```

### `/conserve:optimize-context`
Optimize context window usage.

```bash
# Usage
/optimize-context [--target PERCENT] [--scope PATH]

# Options
--target PERCENT   Target context utilization (default: 50%)
--scope PATH       Limit to specific directory
--suggest          Only show suggestions, don't apply
--aggressive       Apply all optimizations

# Examples
/optimize-context --target 40%
/optimize-context --scope plugins/sanctum/ --suggest
```

### `/conserve:analyze-growth`

**Consolidated:** This command has been merged into `/bloat-scan`. See [bloat-scan](#conservebloat-scan).

~~Analyze skill growth patterns.~~

```bash
# Usage (now use /bloat-scan instead)
/bloat-scan [--level 1|2|3] [--focus TYPE] [--report FILE]

# Previous /analyze-growth options are covered by:
/bloat-scan --level 2 --focus code    # Growth pattern analysis
```

---

## Imbue Plugin

### `/imbue:catchup`
Quick context recovery after session restart.

```bash
# Usage
/catchup [--depth LEVEL] [--focus AREA]

# Options
--depth LEVEL    Recovery depth: shallow|standard|deep (default: standard)
--focus AREA     Focus on: git|docs|issues|all
--since DATE     Catch up from specific date

# Examples
/catchup                           # Standard recovery
/catchup --depth deep              # Full context recovery
/catchup --focus git --since "3 days ago"
```

### `/imbue:feature-review`

**Consolidated:** This command has been merged into `Skill(imbue:scope-guard)`. Invoke via `Skill(imbue:scope-guard)` instead.

~~Feature prioritization and gap analysis.~~

```bash
# Usage (now use Skill(imbue:scope-guard) instead)
Skill(imbue:scope-guard)

# scope-guard covers feature prioritization, gap analysis,
# and anti-overengineering evaluation
```

### `/imbue:structured-review`
Structured review workflow with methodology options.

```bash
# Usage
/structured-review PATH [--methodology METHOD]

# Options
--methodology METHOD    Review methodology: evidence-based|checklist|formal
--todos                 Generate TodoWrite items
--summary              Include executive summary

# Examples
/structured-review plugins/sanctum/ --methodology evidence-based
/structured-review . --todos --summary
```

---

## Sanctum Plugin

### `/sanctum:prepare-pr` (alias: `/pr`)
Complete PR preparation workflow.

```bash
# Usage
/prepare-pr [--no-code-review] [--reviewer-scope SCOPE] [--skip-updates] [FILE]
/pr [options...]  # Alias

# Options
--no-code-review           Skip automated code review (faster)
--reviewer-scope SCOPE     Review strictness: strict|standard|lenient
--skip-updates             Skip documentation/test updates (Phase 0)
FILE                       Output file for PR description (default: pr_description.md)

# Reviewer Scope Levels
# strict   - All suggestions must be addressed
# standard - Critical issues must be fixed, suggestions are recommendations
# lenient  - Focus on blocking issues only

# Examples
/prepare-pr                                    # Full workflow
/pr                                            # Alias for full workflow
/prepare-pr --skip-updates                     # Skip Phase 0 updates
/prepare-pr --no-code-review                   # Skip code review
/prepare-pr --reviewer-scope strict            # Strict review for critical changes
/prepare-pr --skip-updates --no-code-review    # Fastest (legacy behavior)
```

### `/sanctum:commit-msg`
Generate commit message.

```bash
# Usage
/commit-msg [--type TYPE] [--scope SCOPE]

# Options
--type TYPE      Force commit type: feat|fix|docs|refactor|test|chore
--scope SCOPE    Force commit scope
--breaking       Include breaking change footer
--issue N        Reference issue number

# Examples
/commit-msg
/commit-msg --type feat --scope api
/commit-msg --breaking --issue 42
```

### `/sanctum:do-issue`
Fix GitHub issues.

```bash
# Usage
/do-issue ISSUE_NUMBER [--branch NAME]

# Options
--branch NAME    Branch name (default: issue-N)
--auto-merge     Attempt auto-merge after PR
--draft          Create draft PR

# Examples
/do-issue 42
/do-issue 123 --branch fix/auth-bug
/do-issue 99 --draft
```

### `/sanctum:fix-pr`
Address PR review comments.

```bash
# Usage
/fix-pr [PR_NUMBER] [--auto-resolve]

# Options
PR_NUMBER        PR number (default: current branch's PR)
--auto-resolve   Auto-resolve addressed comments
--batch          Address all comments in batch
--interactive    Address one comment at a time

# Examples
/fix-pr 42
/fix-pr --auto-resolve
/fix-pr 42 --batch
```

### `/sanctum:fix-workflow`
Workflow retrospective with automatic improvement context.

```bash
# Usage
/fix-workflow [WORKFLOW_NAME] [--context]

# Options
WORKFLOW_NAME    Specific workflow to analyze
--context        Gather improvement context automatically
--lessons        Generate lessons learned
--improvements   Suggest workflow improvements

# Examples
/fix-workflow pr-review --context
/fix-workflow --lessons --improvements
```

### `/sanctum:pr-review`
Enhanced PR review.

```bash
# Usage
/pr-review [PR_NUMBER] [--thorough]

# Options
PR_NUMBER    PR to review (default: current)
--thorough   Deep review with all checks
--quick      Fast review of critical issues only
--security   Security-focused review

# Examples
/pr-review 42
/pr-review --thorough
/pr-review --quick --security
```

### `/sanctum:update-docs`
Update project documentation.

```bash
# Usage
/update-docs [--scope SCOPE] [--check]

# Options
--scope SCOPE    Scope: all|api|readme|guides
--check          Check only, don't modify
--sync           Sync with code changes

# Examples
/update-docs
/update-docs --scope api
/update-docs --check
```

### `/sanctum:update-readme`

**Consolidated:** This command has been merged into `/update-docs`. See [update-docs](#sanctumupdate-docs). Use `/update-docs --scope readme` for README-specific updates.

~~Modernize README.~~

```bash
# Usage (now use /update-docs instead)
/update-docs --scope readme

# Previous /update-readme options are covered by /update-docs:
/update-docs --scope readme    # README-specific updates
/update-docs --scope all       # Full documentation refresh
```

### `/sanctum:update-tests`
Maintain tests.

```bash
# Usage
/update-tests [PATH] [--coverage]

# Options
PATH            Test path to update
--coverage      Ensure coverage targets
--missing       Add missing tests
--modernize     Update to modern patterns

# Examples
/update-tests tests/
/update-tests --missing --coverage
```

### `/sanctum:update-version`
Bump versions.

```bash
# Usage
/update-version [VERSION] [--type TYPE]

# Options
VERSION        Explicit version (e.g., 1.2.3)
--type TYPE    Bump type: major|minor|patch|prerelease
--tag          Create git tag
--push         Push tag to remote

# Examples
/update-version 2.0.0
/update-version --type minor --tag
/update-version --type patch --tag --push
```

### `/sanctum:update-dependencies`
Update project dependencies.

```bash
# Usage
/update-dependencies [--type TYPE] [--dry-run]

# Options
--type TYPE    Dependency type: all|prod|dev|security
--dry-run      Preview updates without applying
--major        Include major version updates
--security     Security updates only

# Examples
/update-dependencies
/update-dependencies --dry-run
/update-dependencies --type security
/update-dependencies --major
```

### `/sanctum:git-catchup`
Git repository catchup.

```bash
# Usage
/git-catchup [--since DATE] [--author AUTHOR]

# Options
--since DATE      Start date for catchup
--author AUTHOR   Filter by author
--branch BRANCH   Specific branch
--format FORMAT   Output format: summary|detailed|log

# Examples
/git-catchup --since "1 week ago"
/git-catchup --author "user@example.com"
```

### `/sanctum:create-tag`
Create git tags for releases.

```bash
# Usage
/create-tag VERSION [--message MSG] [--sign]

# Options
VERSION        Tag version (e.g., v1.0.0)
--message MSG  Tag message
--sign         Create signed tag
--push         Push tag to remote

# Examples
/create-tag v1.0.0
/create-tag v1.0.0 --message "Release 1.0.0" --sign --push
```

---

**Extended plugins**: [Memory Palace, Pensive, Parseltongue, Spec-Kit, Scribe, Scry, Hookify, Leyline](capabilities-commands-extended.md)

**See also**: [Skills](capabilities-skills.md) | [Agents](capabilities-agents.md) | [Hooks](capabilities-hooks.md) | [Workflows](capabilities-workflows.md)
