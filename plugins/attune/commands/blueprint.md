---
name: blueprint
description: "Generate implementation plan with architecture design and dependency-ordered tasks from specification"
usage: /attune:blueprint [--input FILE] [--component NAME]
---

# Attune Plan Command

Transform specifications into executable implementation plans with system architecture, component design, and dependency-ordered task breakdown.

## When To Use

Use this command when you need to:
- Convert specification into implementation plan
- Design system architecture from requirements
- Break down work into dependency-ordered tasks
- Estimate effort and plan sprints
- Define component interfaces and data flow
- Create actionable roadmap for execution

## When NOT To Use

Avoid this command if:
- No specification exists yet (use `/attune:specify` first)
- Still defining requirements (complete specification phase)
- Ready to execute existing plan (use `/attune:execute` instead)
- Adjusting running project (update plan incrementally)

## Usage

```bash
# Create plan from specification
/attune:blueprint

# Plan with custom input
/attune:blueprint --input docs/specification.md

# Focus on specific component
/attune:blueprint --component "authentication"
```

## What This Command Does

1. **Loads specification** from specify phase
2. **Invokes planning skill** with superpowers integration
3. **Designs system architecture** (components, interfaces, data flow)
4. **Breaks down into tasks** with dependencies and estimates
5. **Produces implementation plan** for execution phase

## Integration with Superpowers

When superpowers plugin is available:
- Uses `Skill(superpowers:writing-plans)` for structured planning
- Applies dependency analysis
- Creates checkpoint-based execution flow

Without superpowers:
- Falls back to attune's native planning skill
- Provides similar structured approach
- Documents tasks systematically

## Workflow

```bash
# 1. Invoke planning skill
Skill(attune:project-planning)

# 2. Design architecture:
#    - System components
#    - Component interfaces
#    - Data flow diagrams
#    - Technology selections

# 3. Break down into tasks:
#    - Development tasks with dependencies
#    - Testing tasks
#    - Deployment tasks
#    - Documentation tasks

# 4. Generate implementation plan
#    - Saved to docs/implementation-plan.md
#    - Includes architecture + task breakdown

# 5. Transition to initialization/execution
#    Next: /attune:project-init (set up project)
#    Then: /attune:execute (implement tasks)
```

## Plan Structure

### Section 1: Architecture Design

**Components**:
```markdown
## System Architecture

### Component Diagram
```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Web UI    │─────▶│   API Server │─────▶│  Database   │
│  (React)    │      │   (FastAPI)  │      │ (Postgres)  │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │ GitHub API   │
                     └──────────────┘
```

### Components

#### Component 1: Web UI
**Responsibility**: User interface for debt tracking
**Technology**: React 18 + TypeScript + Vite
**Interfaces**:
- REST API client
- OAuth callback handler
**Data**: Client-side state management (React Context)

#### Component 2: API Server
**Responsibility**: Business logic and GitHub integration
**Technology**: FastAPI + Python 3.10
**Interfaces**:
- REST API endpoints
- GitHub webhook receiver
- Database access layer
**Data**: Issue cache, user sessions

#### Component 3: Database
**Responsibility**: Persistent data storage
**Technology**: PostgreSQL 14
**Schema**:
- users (id, github_id, access_token)
- repositories (id, owner, name)
- debt_items (id, repo_id, issue_number, type, priority)
```

### Section 2: Task Breakdown

**Task Format**:
```markdown
### TASK-001: [Task Name]

**Description**: Clear description of what needs to be done

**Type**: Implementation | Testing | Documentation | Deployment
**Priority**: P0 (Critical) | P1 (High) | P2 (Medium) | P3 (Low)
**Estimate**: [Story points or hours]
**Dependencies**: TASK-002, TASK-005
**Assignee**: [Team member or TBD]

**Acceptance Criteria**:
- [ ] Criterion 1
- [ ] Criterion 2

**Technical Notes**:
- Implementation detail 1
- Implementation detail 2

**Testing Requirements**:
- Unit tests for X
- Integration tests for Y
```

### Section 3: Development Phases

**Phase 1: Foundation** (Weeks 1-2)
- Project initialization
- Database schema
- GitHub OAuth setup
- Basic API scaffolding

**Phase 2: Core Features** (Weeks 3-6)
- Issue discovery
- Prioritization algorithm
- Dashboard implementation

**Phase 3: Polish** (Weeks 7-8)
- Error handling
- Performance optimization
- Documentation

**Phase 4: Launch** (Week 9)
- Deployment
- User testing
- Feedback collection

## Arguments

- `--input <path>` - Input specification (default: docs/specification.md)
- `--output <path>` - Output plan (default: docs/implementation-plan.md)
- `--component <name>` - Focus on specific component
- `--detailed` - Generate detailed task breakdown with code examples

## Examples

### Example 1: Full Project Plan

```bash
/attune:specify
/attune:blueprint
```

**Output**: `docs/implementation-plan.md`

```markdown
# Technical Debt Tracker - Implementation Plan v1.0

**Author**: Project Team
**Date**: 2026-01-02
**Sprint Length**: 2 weeks
**Team Size**: 2 developers

## Architecture

### System Overview

Three-tier architecture:
- Frontend: React SPA
- Backend: FastAPI REST API
- Data: PostgreSQL + GitHub API

### Components

[Component descriptions as shown above]

### Data Flow

1. User authenticates via GitHub OAuth
2. Frontend requests debt items from API
3. API queries cached data from PostgreSQL
4. Background sync updates cache from GitHub
5. Frontend displays prioritized debt list

## Task Breakdown

### Phase 1: Foundation (Sprint 1) - TASK-001 through TASK-010

#### TASK-001: Initialize Project Structure

**Description**: Set up project with proper tooling and CI/CD

**Type**: Implementation
**Priority**: P0
**Estimate**: 4 hours
**Dependencies**: None
**Assignee**: TBD

**Acceptance Criteria**:
- [ ] Python project initialized with uv
- [ ] React project initialized with Vite
- [ ] GitHub Actions workflows configured
- [ ] Pre-commit hooks set up
- [ ] Makefile with dev targets

**Technical Notes**:
- Use /attune:project-init for project setup
- Configure monorepo structure (backend/, frontend/)
- Set up shared Makefile targets

**Testing Requirements**:
- CI pipeline passes
- `make test` runs successfully

#### TASK-002: Database Schema Design

**Description**: Design and implement PostgreSQL schema

**Type**: Implementation
**Priority**: P0
**Estimate**: 6 hours
**Dependencies**: TASK-001
**Assignee**: TBD

**Acceptance Criteria**:
- [ ] Schema defined in migrations/001_initial.sql
- [ ] Users table created
- [ ] Repositories table created
- [ ] Debt_items table created
- [ ] Indexes on foreign keys

**Technical Notes**:
- Use Alembic for migrations
- Design for 1000+ debt items per repository
- Include created_at/updated_at timestamps

**Testing Requirements**:
- Migration applies cleanly
- Can rollback migration
- Constraints enforced (foreign keys, unique)

[... more tasks ...]

### Phase 2: Core Features (Sprints 2-4) - TASK-011 through TASK-030

[... task details ...]

### Phase 3: Polish (Sprint 5) - TASK-031 through TASK-040

[... task details ...]

## Dependency Graph

```
TASK-001 (Init)
    ├─▶ TASK-002 (Database)
    │       ├─▶ TASK-003 (Models)
    │       └─▶ TASK-011 (Issue Import)
    └─▶ TASK-004 (OAuth)
            └─▶ TASK-005 (Auth Middleware)
```

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| GitHub API rate limits | High | Medium | Implement caching, request batching |
| OAuth complexity | Medium | Low | Use proven library (authlib) |
| Performance issues | Medium | Medium | Database indexing, query optimization |

## Success Metrics

- [ ] All P0 tasks completed by Sprint 3
- [ ] 90%+ test coverage
- [ ] CI/CD pipeline green
- [ ] Performance targets met (< 2s dashboard load)
- [ ] Zero P0 bugs in production

## Timeline

| Sprint | Dates | Focus | Deliverable |
|--------|-------|-------|-------------|
| 1 | Jan 3-16 | Foundation | Working dev environment |
| 2 | Jan 17-30 | GitHub Integration | Issue import working |
| 3 | Jan 31-Feb 13 | Prioritization | Algorithm implemented |
| 4 | Feb 14-27 | Dashboard | UI functional |
| 5 | Feb 28-Mar 13 | Polish | Production ready |

## Next Steps

1. **Review plan**: Team walkthrough and adjustments
2. **Initialize project**: Run `/attune:project-init --lang python`
3. **Start Sprint 1**: Execute TASK-001 through TASK-010
4. **Track progress**: Use `/attune:execute` for systematic implementation
```

### Example 2: Component-Focused Plan

```bash
/attune:blueprint --component "authentication"
```

Creates `docs/plans/component-authentication.md` with focused architecture and tasks.

### Example 3: Detailed Plan with Code Examples

```bash
/attune:blueprint --detailed
```

Includes code snippets and implementation examples for each task:

```markdown
#### TASK-003: Implement Data Models

**Code Example**:
```python
# backend/app/models/debt_item.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.db.base import Base

class DebtItem(Base):
    __tablename__ = "debt_items"

    id = Column(Integer, primary_key=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"))
    issue_number = Column(Integer, nullable=False)
    title = Column(String(500), nullable=False)
    debt_type = Column(String(50))  # code, architecture, security, perf
    priority_score = Column(Integer)  # calculated field
    created_at = Column(DateTime, nullable=False)
```
```

## Integration with Full Cycle

```
/attune:brainstorm    ← Generate project brief
      ↓
/attune:specify       ← Define requirements
      ↓
/attune:blueprint          ← You are here
      ↓
/attune:project-init          ← Initialize project structure
      ↓
/attune:execute       ← Implement tasks systematically
```

## Quality Checks

The planning skill automatically validates:
- ✅ All tasks have clear acceptance criteria
- ✅ Dependencies are acyclic (no circular dependencies)
- ✅ Estimates are provided
- ✅ Critical path identified
- ✅ Risk mitigation strategies documented

## Related Commands

- `/attune:specify` - Create specification
- `/attune:project-init` - Initialize project from plan
- `/attune:execute` - Execute implementation tasks
- `/speckit-plan` - Spec-kit's planning workflow (if available)
- `/speckit-tasks` - Spec-kit's task generation (if available)

## Related Skills

- `Skill(attune:project-planning)` - Planning methodology
- `Skill(superpowers:writing-plans)` - Structured planning (if available)
- `Skill(spec-kit:task-planning)` - Task breakdown (if available)

## Superpowers Integration

When superpowers is installed, this command automatically:
- Invokes `Skill(superpowers:writing-plans)` for planning framework
- Uses dependency analysis patterns
- Creates checkpoint-based execution flow

Check if superpowers is available:
```bash
/plugin list | grep superpowers
```

Install superpowers:
```bash
/plugin marketplace add obra/superpowers
/plugin install superpowers@superpowers-marketplace
```
