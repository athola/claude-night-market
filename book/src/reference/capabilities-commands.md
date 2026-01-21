# Command Reference

Full flag and option documentation for all commands in the Claude Night Market ecosystem.

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

**Workflow Example:**
```bash
# Before submitting a plugin PR
/abstract:validate-plugin my-plugin --strict
# Review any issues found
# Fix problems, then re-validate
/abstract:validate-plugin my-plugin --fix
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

**Workflow Example:**
```bash
# Start a new Python project
mkdir my-awesome-project && cd my-awesome-project
/attune:init --lang python --name my-awesome-project

# After initialization
make dev-setup  # Install dependencies, set up pre-commit
make help       # See all available targets
make test       # Verify setup works
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

### `/attune:plan`
Plan architecture and break down tasks.

```bash
# Usage
/attune:plan [--from BRAINSTORM] [--output FILE]

# Options
--from FILE      Use brainstorm results as input
--output FILE    Save plan to file
--depth LEVEL    Planning depth: high|detailed|exhaustive
--include        Include specific aspects: tests|ci|docs

# Examples
/attune:plan --from brainstorm.md --depth detailed
/attune:plan --include tests,ci
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

**Workflow Example:**
```bash
# Pre-release cleanup workflow
/bloat-scan --level 2                 # Find issues
git checkout -b cleanup/bloat-reduction
/unbloat --approve high-priority      # Fix high-priority items
make test                             # Verify no regressions
/prepare-pr                           # Create cleanup PR
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
Analyze skill growth patterns.

```bash
# Usage
/analyze-growth [--plugin PLUGIN] [--days N] [--trend]

# Options
--plugin PLUGIN    Limit to specific plugin
--days N           Analysis period (default: 30)
--trend            Show growth trend predictions
--alert            Alert if growth exceeds threshold

# Examples
/analyze-growth --plugin conserve --days 60
/analyze-growth --trend --alert
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
Feature prioritization and gap analysis.

```bash
# Usage
/feature-review [--scope BRANCH] [--against BASELINE]

# Options
--scope BRANCH     Review specific branch
--against BASELINE Compare against baseline (main|tag|commit)
--gaps             Focus on gap analysis
--priorities       Generate priority rankings

# Examples
/feature-review --scope feature/new-api
/feature-review --gaps --against main
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

## Memory Palace Plugin

### `/memory-palace:garden`
Manage digital gardens.

```bash
# Usage
/garden [ACTION] [--path PATH]

# Actions
tend           Review and update garden entries
prune          Remove stale/low-value entries
cultivate      Add new entries from queue
status         Show garden health metrics

# Options
--path PATH    Garden path (default: docs/knowledge-corpus/)
--dry-run      Preview changes
--score N      Minimum score threshold for cultivation

# Examples
/garden tend                    # Review garden entries
/garden prune --dry-run         # Preview what would be removed
/garden cultivate --score 70    # Add high-quality entries
/garden status                  # Show health metrics
```

### `/memory-palace:navigate`
Search across knowledge palaces.

```bash
# Usage
/navigate QUERY [--scope SCOPE] [--type TYPE]

# Options
--scope SCOPE    Search scope: local|corpus|all
--type TYPE      Content type: docs|code|web|all
--limit N        Maximum results (default: 10)
--relevance N    Minimum relevance score

# Examples
/navigate "authentication patterns" --scope corpus
/navigate "pytest fixtures" --type docs --limit 5
```

### `/memory-palace:palace`
Manage knowledge palaces.

```bash
# Usage
/palace [ACTION] [PALACE_NAME]

# Actions
create NAME    Create new palace
list           List all palaces
status NAME    Show palace status
archive NAME   Archive palace

# Options
--template TEMPLATE    Palace template: session|project|topic
--from FILE           Initialize from existing content

# Examples
/palace create project-x --template project
/palace list
/palace status project-x
/palace archive old-project
```

### `/memory-palace:review-room`
Review items in the knowledge queue.

```bash
# Usage
/review-room [--status STATUS] [--source SOURCE]

# Options
--status STATUS    Filter by status: pending|approved|rejected
--source SOURCE    Filter by source: webfetch|websearch|manual
--batch N          Review N items at once
--auto-score       Auto-generate scores

# Examples
/review-room --status pending --batch 10
/review-room --source webfetch --auto-score
```

---

## Parseltongue Plugin

### `/parseltongue:analyze-tests`
Test suite health report.

```bash
# Usage
/analyze-tests [PATH] [--coverage] [--flaky]

# Options
--coverage    Include coverage analysis
--flaky       Detect potentially flaky tests
--slow N      Flag tests slower than N seconds
--missing     Find untested code

# Examples
/analyze-tests tests/ --coverage
/analyze-tests --flaky --slow 5
/analyze-tests src/api/ --missing
```

### `/parseltongue:run-profiler`
Profile code execution.

```bash
# Usage
/run-profiler [COMMAND] [--type TYPE]

# Options
--type TYPE    Profiler type: cpu|memory|line|call
--output FILE  Output file for profile data
--flame        Generate flame graph
--top N        Show top N hotspots

# Examples
/run-profiler "python main.py" --type cpu
/run-profiler "pytest tests/" --type memory --flame
/run-profiler --type line --top 20
```

### `/parseltongue:check-async`
Async pattern validation.

```bash
# Usage
/check-async [PATH] [--strict]

# Options
--strict      Strict async compliance
--suggest     Suggest async improvements
--blocking    Find blocking calls in async code

# Examples
/check-async src/ --strict
/check-async --blocking --suggest
```

---

## Pensive Plugin

### `/pensive:full-review`
Unified code review.

```bash
# Usage
/full-review [PATH] [--scope SCOPE] [--output FILE]

# Options
--scope SCOPE    Review scope: changed|staged|all
--output FILE    Save review to file
--severity MIN   Minimum severity: critical|high|medium|low
--categories     Include categories: bugs|security|style|perf

# Examples
/full-review src/ --scope staged
/full-review --scope changed --severity high
/full-review . --output review.md --categories bugs,security
```

### `/pensive:code-review`
Expert code review.

```bash
# Usage
/code-review [FILES...] [--focus FOCUS]

# Options
--focus FOCUS    Focus area: bugs|api|tests|security|style
--evidence       Include evidence logging
--lsp            Enable LSP-enhanced review (requires ENABLE_LSP_TOOL=1)

# Examples
/code-review src/api.py --focus bugs
/code-review --focus security --evidence
ENABLE_LSP_TOOL=1 /code-review src/ --lsp
```

### `/pensive:architecture-review`
Architecture assessment.

```bash
# Usage
/architecture-review [PATH] [--depth DEPTH]

# Options
--depth DEPTH    Analysis depth: surface|standard|deep
--patterns       Identify architecture patterns
--anti-patterns  Flag anti-patterns
--suggestions    Generate improvement suggestions

# Examples
/architecture-review src/ --depth deep
/architecture-review --patterns --anti-patterns
```

### `/pensive:rust-review`
Rust-specific review.

```bash
# Usage
/rust-review [PATH] [--safety]

# Options
--safety     Focus on unsafe code analysis
--lifetimes  Analyze lifetime patterns
--memory     Memory safety review
--perf       Performance-focused review

# Examples
/rust-review src/lib.rs --safety
/rust-review --lifetimes --memory
```

### `/pensive:test-review`
Test quality review.

```bash
# Usage
/test-review [PATH] [--coverage]

# Options
--coverage     Include coverage analysis
--patterns     Review test patterns (AAA, BDD)
--flaky        Detect flaky test patterns
--gaps         Find testing gaps

# Examples
/test-review tests/ --coverage
/test-review --patterns --gaps
```

### `/pensive:shell-review`
Shell script safety and portability review.

```bash
# Usage
/shell-review [FILES...] [--strict]

# Options
--strict       Strict POSIX compliance
--security     Security-focused review
--portability  Check cross-shell compatibility

# Examples
/shell-review scripts/*.sh --strict
/shell-review --security install.sh
```

### `/pensive:skill-review`
Analyze skill runtime metrics and stability. This is the canonical command for
skill performance analysis (execution counts, success rates, stability gaps).

For static quality analysis (frontmatter, structure), use `abstract:skill-auditor`.

```bash
# Usage
/skill-review [--plugin PLUGIN] [--recommendations]

# Options
--plugin PLUGIN      Limit to specific plugin
--all-plugins        Aggregate metrics across all plugins
--unstable-only      Only show skills with stability_gap > 0.3
--skill NAME         Deep-dive specific skill
--recommendations    Generate improvement recommendations

# Examples
/skill-review --plugin sanctum
/skill-review --unstable-only
/skill-review --skill imbue:proof-of-work
/skill-review --all-plugins --recommendations
```

**Stability Gap**: The key metric - measures consistency between average and worst-case performance:
- `< 0.2`: Stable (consistent performance)
- `0.2 - 0.3`: Warning (occasional issues)
- `> 0.3`: Unstable (needs attention)

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

**Workflow Example:**
```bash
# Standard feature PR workflow
git add .
/prepare-pr
# Review generated PR description
gh pr create --body-file pr_description.md

# Quick PR for small fix
git add .
/prepare-pr --skip-updates --reviewer-scope lenient
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
Modernize README.

```bash
# Usage
/update-readme [--badges] [--toc]

# Options
--badges    Update/add badges
--toc       Update table of contents
--examples  Update code examples
--full      Full README refresh

# Examples
/update-readme
/update-readme --badges --toc
/update-readme --full
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

## Spec-Kit Plugin

### `/speckit-startup`
Bootstrap specification workflow.

```bash
# Usage
/speckit-startup [--dir DIR]

# Options
--dir DIR    Specification directory (default: .specify/)
--template   Use template structure
--minimal    Minimal specification setup

# Examples
/speckit-startup
/speckit-startup --dir specs/
/speckit-startup --minimal
```

### `/speckit-clarify`
Generate clarifying questions.

```bash
# Usage
/speckit-clarify [TOPIC] [--rounds N]

# Options
TOPIC        Topic to clarify
--rounds N   Number of question rounds
--depth      Deep clarification
--technical  Technical focus

# Examples
/speckit-clarify "user authentication"
/speckit-clarify --rounds 3 --technical
```

### `/speckit-specify`
Create specification.

```bash
# Usage
/speckit-specify [--from FILE] [--output DIR]

# Options
--from FILE    Input source (brainstorm, requirements)
--output DIR   Output directory
--type TYPE    Spec type: full|api|data|ui

# Examples
/speckit-specify --from requirements.md
/speckit-specify --type api --output .specify/
```

### `/speckit-plan`
Generate implementation plan.

```bash
# Usage
/speckit-plan [--from SPEC] [--phases]

# Options
--from SPEC    Source specification
--phases       Include phase breakdown
--estimates    Include time estimates
--dependencies Show task dependencies

# Examples
/speckit-plan --from .specify/spec.md
/speckit-plan --phases --estimates
```

### `/speckit-tasks`
Generate task breakdown.

```bash
# Usage
/speckit-tasks [--from PLAN] [--parallel]

# Options
--from PLAN      Source plan
--parallel       Mark parallelizable tasks
--granularity    Task granularity: coarse|medium|fine
--assignable     Make tasks assignable

# Examples
/speckit-tasks --from .specify/plan.md
/speckit-tasks --parallel --granularity fine
```

### `/speckit-implement`
Execute implementation plan.

```bash
# Usage
/speckit-implement [--phase PHASE] [--task ID] [--continue]

# Options
--phase PHASE   Execute specific phase
--task ID       Execute specific task
--continue      Resume from checkpoint
--parallel      Enable parallel execution

# Examples
/speckit-implement --phase setup
/speckit-implement --task T1.2
/speckit-implement --continue
```

### `/speckit-checklist`
Generate implementation checklist.

```bash
# Usage
/speckit-checklist [--type TYPE] [--output FILE]

# Options
--type TYPE    Checklist type: ux|test|security|deployment
--output FILE  Output file
--interactive  Interactive completion mode

# Examples
/speckit-checklist --type security
/speckit-checklist --type ux --output checklists/ux.md
```

### `/speckit-analyze`
Check artifact consistency.

```bash
# Usage
/speckit-analyze [--strict] [--fix]

# Options
--strict    Strict consistency checking
--fix       Auto-fix inconsistencies
--report    Generate consistency report

# Examples
/speckit-analyze
/speckit-analyze --strict --report
```

---

## Scribe Plugin

### `/slop-scan`
Scan files for AI-generated content markers.

```bash
# Usage
/slop-scan [PATH] [--fix] [--report FILE]

# Options
PATH          File or directory to scan (default: current directory)
--fix         Show fix suggestions
--report FILE Output to report file

# Examples
/slop-scan
/slop-scan docs/
/slop-scan README.md --fix
/slop-scan **/*.md --report slop-report.md
```

### `/style-learn`
Create style profile from examples.

```bash
# Usage
/style-learn [FILES] --name NAME

# Options
FILES         Example files to learn from
--name NAME   Profile name
--merge       Merge with existing profile

# Examples
/style-learn good-examples/*.md --name house-style
/style-learn docs/api.md --name api-docs --merge
```

### `/doc-polish`
Clean up AI-generated content.

```bash
# Usage
/doc-polish [FILES] [--style NAME] [--dry-run]

# Options
FILES         Files to polish
--style NAME  Apply learned style
--dry-run     Preview changes without writing

# Examples
/doc-polish README.md
/doc-polish docs/*.md --style house-style
/doc-polish **/*.md --dry-run
```

### `/doc-generate`
Generate new documentation.

```bash
# Usage
/doc-generate TYPE [--style NAME] [--output FILE]

# Options
TYPE          Document type: readme|api|changelog|usage
--style NAME  Apply learned style
--output FILE Output file path

# Examples
/doc-generate readme
/doc-generate api --style api-docs
/doc-generate changelog --output CHANGELOG.md
```

### `/doc-verify`
Validate documentation claims with proof-of-work.

```bash
# Usage
/doc-verify [FILES] [--strict] [--report FILE]

# Options
FILES         Files to verify
--strict      Treat warnings as errors
--report FILE Output QA report

# Examples
/doc-verify README.md
/doc-verify docs/ --strict
/doc-verify **/*.md --report qa-report.md
```

---

## Scry Plugin

### `/scry:record-terminal`
Create terminal recording.

```bash
# Usage
/record-terminal [COMMAND] [--output FILE] [--format FORMAT]

# Options
COMMAND         Command to record
--output FILE   Output file (default: recording.gif)
--format FORMAT Output format: gif|svg|mp4|tape
--width N       Terminal width
--height N      Terminal height
--speed N       Playback speed multiplier

# Examples
/record-terminal "make test" --output demo.gif
/record-terminal --format svg --width 80 --height 24
```

### `/scry:record-browser`
Record browser session.

```bash
# Usage
/record-browser [URL] [--output FILE] [--actions FILE]

# Options
URL             Starting URL
--output FILE   Output file
--actions FILE  Playwright actions script
--headless      Run headless
--viewport WxH  Viewport size

# Examples
/record-browser "http://localhost:3000" --output demo.mp4
/record-browser --actions test-flow.js --headless
```

---

## Hookify Plugin

### `/hookify:install`
Install hooks.

```bash
# Usage
/hookify:install [HOOK_NAME] [--plugin PLUGIN]

# Options
HOOK_NAME       Specific hook to install
--plugin PLUGIN Install hooks from plugin
--all           Install all available hooks
--dry-run       Preview installation

# Examples
/hookify:install memory-palace-web-processor
/hookify:install --plugin conserve
/hookify:install --all --dry-run
```

### `/hookify:configure`
Configure hook settings.

```bash
# Usage
/hookify:configure [HOOK_NAME] [--enable|--disable] [--set KEY=VALUE]

# Options
HOOK_NAME         Hook to configure
--enable          Enable hook
--disable         Disable hook
--set KEY=VALUE   Set configuration value
--reset           Reset to defaults

# Examples
/hookify:configure memory-palace --set research_mode=cache_first
/hookify:configure context-warning --disable
```

### `/hookify:list`
List installed hooks.

```bash
# Usage
/hookify:list [--plugin PLUGIN] [--status]

# Options
--plugin PLUGIN  Filter by plugin
--status         Show enabled/disabled status
--verbose        Show full configuration

# Examples
/hookify:list
/hookify:list --plugin memory-palace --status
```

---

## Leyline Plugin

### `/leyline:reinstall-all-plugins`
Refresh all plugins.

```bash
# Usage
/reinstall-all-plugins [--force] [--clean]

# Options
--force    Force reinstall even if up-to-date
--clean    Clean install (remove then reinstall)
--verify   Verify installation after reinstall

# Examples
/reinstall-all-plugins
/reinstall-all-plugins --clean --verify
```

### `/leyline:update-all-plugins`
Update all plugins.

```bash
# Usage
/update-all-plugins [--check] [--exclude PLUGINS]

# Options
--check           Check for updates only
--exclude PLUGINS Comma-separated plugins to skip
--major           Include major version updates

# Examples
/update-all-plugins
/update-all-plugins --check
/update-all-plugins --exclude "experimental,beta"
```

---

**See also**: [Skills](capabilities-skills.md) | [Agents](capabilities-agents.md) | [Hooks](capabilities-hooks.md) | [Workflows](capabilities-workflows.md)
