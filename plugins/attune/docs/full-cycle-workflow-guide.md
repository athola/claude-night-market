# Full-Cycle Workflow Guide

Complete guide to using Attune's brainstorm-plan-execute workflow for systematic project development.

## Overview

Attune provides a structured approach to project development:

```
IDEATION → SPECIFICATION → PLANNING → INITIALIZATION → IMPLEMENTATION
```

This prevents common development pitfalls:
- ❌ Scope creep from unclear requirements
- ❌ Rework from poor architecture decisions
- ❌ Technical debt from ad-hoc implementation
- ❌ Lost progress from missing tracking

## The Five Phases

### Phase 1: Brainstorm (/attune:brainstorm)

**Purpose**: Transform vague ideas into concrete project briefs

**Activities**:
1. Problem definition through Socratic questioning
2. Constraint identification (technical, resources, compliance)
3. Approach generation (3-5 alternatives)
4. Trade-off analysis and decision making
5. Project brief documentation

**Output**: `docs/project-brief.md`

**Example Session**:
```bash
/attune:brainstorm --domain "web application"

# Interactive Q&A:
→ What problem are you solving?
  "Development teams can't track technical debt systematically"

→ Who experiences this problem?
  "Engineering teams, tech leads, managers"

→ What constraints exist?
  "Must integrate with GitHub, 3-month timeline, 2 developers"

# Generates 4 approaches:
1. Standalone SaaS (Django + React)
2. GitHub App integration
3. CLI tool with web dashboard
4. Browser extension

# You select: GitHub App (best integration, lowest friction)

# Output: Complete project brief with selected approach
```

**When to Use**:
- Starting completely new project
- Unclear on requirements or approach
- Multiple stakeholders with different visions
- Need to compare alternatives systematically

**Superpowers Integration**:
- Uses `Skill(superpowers:brainstorming)` for Socratic method
- Applies structured ideation frameworks
- Documents decisions systematically

### Phase 2: Specify (/attune:specify)

**Purpose**: Transform project brief into detailed, testable specifications

**Activities**:
1. Extract functional requirements from brief
2. Define non-functional requirements (performance, security, etc.)
3. Create acceptance criteria (Given-When-Then format)
4. Identify out-of-scope items (prevent scope creep)
5. Clarify ambiguities through Q&A

**Output**: `docs/specification.md`

**Example Session**:
```bash
/attune:specify

# Reads docs/project-brief.md
# Generates structured requirements:

### FR-001: GitHub Issue Discovery
**Acceptance Criteria**:
- [ ] Given repository with issues, when scanning, then import all tech-debt labels
- [ ] Given imported issues, when categorizing, then assign debt type
- [ ] Given categorized issues, when displaying, then group by type and priority

### NFR-001: Performance
- Dashboard loads in < 2 seconds for repos with < 1000 issues
- Sync with GitHub every 15 minutes
- Support 10+ concurrent users

# Optional clarification:
/attune:specify --clarify

# Asks questions about ambiguities:
→ FR-001: What if issue has no label but mentions "debt" in description?
→ NFR-001: Does "< 2 seconds" include authentication or just dashboard load?
```

**When to Use**:
- After brainstorming completes
- Need testable requirements for implementation
- Planning validation and testing strategy
- Communicating requirements to team

**Spec-Kit Integration**:
- Uses `Skill(spec-kit:spec-writing)` for methodology
- Applies spec-kit templates and validation
- Enables clarification workflow

### Phase 3: Plan (/attune:plan)

**Purpose**: Transform specification into implementation plan with architecture and tasks

**Activities**:
1. Design system architecture (components, interfaces)
2. Create data model
3. Select technology stack
4. Break down into dependency-ordered tasks
5. Estimate effort and plan sprints
6. Assess risks and mitigations

**Output**: `docs/implementation-plan.md`

**Example Session**:
```bash
/attune:plan

# Analyzes docs/specification.md
# Invokes project-architect agent

# Generates architecture:
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Web UI    │─────▶│   API Server │─────▶│  Database   │
│  (React)    │      │   (FastAPI)  │      │ (Postgres)  │
└─────────────┘      └──────────────┘      └─────────────┘

# Breaks into tasks:
TASK-001: Initialize Project (4h, P0)
TASK-002: Database Schema (6h, P0, depends: TASK-001)
TASK-003: Data Models (4h, P0, depends: TASK-002)
...

# Groups into sprints:
Sprint 1 (Jan 3-16): Foundation - 10 tasks, 40 points
Sprint 2 (Jan 17-30): GitHub Integration - 12 tasks, 48 points
...
```

**When to Use**:
- After specification completes
- Need system architecture design
- Need task breakdown for team
- Planning resource allocation

**Superpowers Integration**:
- Uses `Skill(superpowers:writing-plans)` for planning
- Applies dependency analysis
- Creates checkpoint-based execution flow

### Phase 4: Initialize (/attune:init)

**Purpose**: Set up project structure with proper tooling and CI/CD

**Activities**:
1. Create project directory structure
2. Initialize git repository
3. Generate language-specific configuration (pyproject.toml, etc.)
4. Set up GitHub Actions workflows
5. Configure pre-commit hooks
6. Create Makefile with development targets
7. Generate README and documentation stubs

**Output**: Complete project structure ready for implementation

**Example Session**:
```bash
/attune:init --lang python --name tech-debt-tracker

# Creates:
tech-debt-tracker/
├── .git/
├── .gitignore
├── .pre-commit-config.yaml
├── pyproject.toml
├── Makefile
├── README.md
├── src/
│   └── tech_debt_tracker/
│       └── __init__.py
├── tests/
│   └── __init__.py
├── docs/                    # Already has brief, spec, plan!
│   ├── project-brief.md
│   ├── specification.md
│   └── implementation-plan.md
└── .github/
    └── workflows/
        ├── test.yml
        ├── lint.yml
        └── typecheck.yml

# Verify setup:
make help
make dev-setup    # Install dependencies, pre-commit
make test         # Run tests (none yet, but framework ready)
```

**When to Use**:
- After planning completes
- Ready to start implementation
- Need consistent project structure
- Setting up CI/CD from start

**Note**: Can be used standalone without prior phases for quick project setup.

### Phase 5: Execute (/attune:execute)

**Purpose**: Systematically implement tasks with TDD, checkpoints, and tracking

**Activities**:
1. Load task list from implementation plan
2. Execute tasks in dependency order
3. Apply TDD workflow (RED → GREEN → REFACTOR)
4. Validate against acceptance criteria
5. Track progress and velocity
6. Report status and identify blockers

**Output**: Working implementation with tests and progress tracking

**Example Session**:
```bash
/attune:execute

# Invokes project-implementer agent
# Loads docs/implementation-plan.md

🚀 Executing Implementation Plan

[✓] TASK-001: Initialize Project Structure (45 min)
    ├─ Project initialized with /attune:init
    ├─ Tests passing: 0 (framework only)
    └─ Status: Complete

[▶] TASK-002: Database Schema Design (in progress)
    ├─ Creating migrations/001_initial.sql
    ├─ Tests: test_schema_creation (RED - failing)
    ├─ Implementing: alembic migration
    └─ Progress: 60%

# TDD Workflow for each task:
# RED: Write test that fails
def test_debt_item_creation(db_session):
    item = DebtItem(title="Fix bug", debt_type="code")
    db_session.add(item)
    db_session.commit()
    assert item.id is not None  # FAILS - table doesn't exist

# GREEN: Minimal implementation
# Create migration, apply schema
# Test now PASSES

# REFACTOR: Improve code quality
# Add indexes, constraints, optimize

# Checkpoint: Task complete
✅ TASK-002: Database Schema Design (90 min)
    ├─ Migration created and applied
    ├─ Tests passing: 5/5
    ├─ Coverage: 95%
    └─ Next: TASK-003

# Daily standup report:
## Yesterday
- ✅ TASK-001 (45 min)
- ✅ TASK-002 (90 min)

## Today
- 🔄 TASK-003: Data Models (60% complete)
- 📋 TASK-004: OAuth Setup (planned)

## Blockers
- None

## Metrics
- Sprint 1 progress: 12/40 tasks (30%)
- Velocity: 3.5 tasks/day
- On track for Sprint 1 completion
```

**When to Use**:
- After project initialization
- Ready for systematic implementation
- Want TDD workflow enforcement
- Need progress tracking and reporting

**Superpowers Integration**:
- Uses `Skill(superpowers:executing-plans)` for execution
- Uses `Skill(superpowers:test-driven-development)` for TDD
- Uses `Skill(superpowers:systematic-debugging)` for blockers
- Uses `Skill(superpowers:verification-before-completion)` for validation

## Workflow Variations

### Full Cycle (Recommended for New Projects)

```bash
/attune:brainstorm → /attune:specify → /attune:plan → /attune:init → /attune:execute
```

**Best for**: Greenfield projects, unclear requirements, team projects

### Quick Start (Skip Early Phases)

```bash
/attune:init → /attune:execute
```

**Best for**: Well-understood projects, prototypes, solo development

### Specification-First (Skip Brainstorm)

```bash
/attune:specify → /attune:plan → /attune:init → /attune:execute
```

**Best for**: Requirements already clear, need planning and execution

### Planning-Only (Existing Projects)

```bash
/attune:plan → /attune:execute
```

**Best for**: Existing projects needing systematic implementation

## Integration Patterns

### With Superpowers

**Enhanced workflow**:
1. Brainstorm uses Socratic method
2. Planning uses structured planning
3. Execution uses TDD and systematic debugging
4. Verification before completion at checkpoints

**Installation**:
```bash
/plugin marketplace add obra/superpowers
/plugin install superpowers@superpowers-marketplace
```

### With Spec-Kit

**Enhanced workflow**:
1. Specification uses spec-writing methodology
2. Planning uses task-planning patterns
3. Implementation aligns with spec-kit executor

**Installation**:
```bash
/plugin install spec-kit@claude-night-market
```

### Standalone (No Dependencies)

**Graceful degradation**:
- All phases work without superpowers or spec-kit
- Built-in methodologies provide similar structure
- Slightly less automation, but same systematic approach

## Best Practices

### 1. Don't Skip Phases for Complex Projects

**Bad**:
```bash
/attune:init  # Jump straight to code
# Result: Scope creep, unclear requirements, rework
```

**Good**:
```bash
/attune:brainstorm  # Explore problem space
/attune:specify     # Define requirements
/attune:plan        # Design architecture
/attune:init        # Set up project
/attune:execute     # Implement systematically
# Result: Clear direction, quality built-in
```

### 2. Iterate Within Phases

**Specification clarification**:
```bash
/attune:specify
# Review output
/attune:specify --clarify
# Answer clarification questions
# Repeat until clear
```

**Planning refinement**:
```bash
/attune:plan
# Review architecture
# Adjust and re-run if needed
```

### 3. Use Execution State for Long Projects

```bash
# Day 1
/attune:execute
# Complete 5 tasks, checkpoint saved

# Day 2
/attune:execute --resume
# Continue from last checkpoint

# Day 3
/attune:execute --task TASK-020
# Jump to specific task if needed
```

### 4. Track Progress Systematically

**Daily standups**:
```bash
/attune:execute
# Generates daily standup report automatically
```

**Sprint reviews**:
```bash
# Check execution state
cat .attune/execution-state.json | jq '.metrics'
# {
#   "tasks_complete": 25,
#   "tasks_total": 40,
#   "completion_percent": 62.5,
#   "velocity_tasks_per_day": 4.2,
#   "estimated_completion_date": "2026-02-10"
# }
```

### 5. Document Blockers and Decisions

When blocked:
```bash
# Systematic debugging:
1. Reproduce issue with failing test
2. Hypothesize causes (3-5 possibilities)
3. Test each hypothesis
4. Document solution in plan or docs/
5. Update execution state
```

## Common Pitfalls

### ❌ Skipping Brainstorming for Vague Ideas

**Problem**: Jump to code without exploring problem space
**Solution**: Use brainstorming to clarify problem, constraints, and approach

### ❌ Ambiguous Specifications

**Problem**: Requirements like "fast" or "user-friendly"
**Solution**: Use specification clarification to make testable

### ❌ No Acceptance Criteria

**Problem**: Don't know when task is complete
**Solution**: All tasks must have Given-When-Then criteria

### ❌ Ignoring Dependencies

**Problem**: Implement tasks out of order
**Solution**: Follow dependency graph from plan

### ❌ Skipping Tests

**Problem**: Write code without tests
**Solution**: TDD enforced - RED → GREEN → REFACTOR

## Success Stories

### Project: Technical Debt Tracker

**Approach**: Full cycle
**Timeline**: 3 months, 2 developers
**Results**:
- ✅ Brainstorming identified GitHub App as best approach
- ✅ Specification had 25 FRs with acceptance criteria
- ✅ Planning broke into 40 tasks across 5 sprints
- ✅ Execution tracked with 92% velocity accuracy
- ✅ Delivered on time with 90% test coverage

### Project: CLI Tool

**Approach**: Quick start (init + execute)
**Timeline**: 1 week, solo developer
**Results**:
- ✅ Project initialized in 5 minutes
- ✅ TDD workflow kept quality high
- ✅ 15 tasks completed systematically
- ✅ Clean codebase, ready for users

## Next Steps

1. **Try the workflow**: Start with a small project using full cycle
2. **Adjust to fit**: Some teams skip phases, others iterate more
3. **Integrate plugins**: Add superpowers and spec-kit for enhanced workflow
4. **Provide feedback**: Help improve attune workflows

## Related Documentation

- [Brainstorm Command](../commands/brainstorm.md)
- [Specify Command](../commands/specify.md)
- [Plan Command](../commands/plan.md)
- [Execute Command](../commands/execute.md)
- [Superpowers Integration](../../docs/superpowers-integration.md)
- [Spec-Kit Integration](../../book/src/reference/superpowers-integration.md)
