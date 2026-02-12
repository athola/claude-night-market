# Command Reference — Extended Plugins

Flag and option documentation for extended plugin commands (memory-palace, parseltongue, pensive, spec-kit, scribe, scry, hookify, leyline).

**Core plugins**: [Abstract, Attune, Conserve, Imbue, Sanctum](capabilities-commands.md)

**See also**: [Capabilities Reference](capabilities-reference.md) | [Skills](capabilities-skills.md) | [Agents](capabilities-agents.md) | [Hooks](capabilities-hooks.md) | [Workflows](capabilities-workflows.md)

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

**Core plugins**: [Abstract, Attune, Conserve, Imbue, Sanctum](capabilities-commands.md)

**See also**: [Skills](capabilities-skills.md) | [Agents](capabilities-agents.md) | [Hooks](capabilities-hooks.md) | [Workflows](capabilities-workflows.md)
