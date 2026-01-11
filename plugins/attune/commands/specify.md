---
name: specify
description: Create specifications from brainstorm using spec-driven development
usage: /attune:specify [--input FILE] [--feature NAME]
---

# Attune Specify Command

<identification>
triggers: specify, create spec, specification, project spec

use_when:
- Transforming brainstorm into detailed specification
- Creating testable requirements from project brief
</identification>

Transform project brief into detailed, testable specification using spec-driven development methodology.

## Usage

```bash
# Create specification from brainstorm output
/attune:specify

# Specify with custom input
/attune:specify --input docs/project-brief.md

# Generate specification for specific feature
/attune:specify --feature "user authentication"
```

## What This Command Does

1. **Loads project brief** from brainstorm phase
2. **Invokes specification skill** with spec-kit integration
3. **Generates detailed requirements** using structured format
4. **Creates testable acceptance criteria**
5. **Produces specification document** for planning phase

## Integration with Spec-Kit

When spec-kit plugin is available:
- Uses `Skill(spec-kit:spec-writing)` for specification methodology
- Applies structured requirement templates
- Ensures testable acceptance criteria

Without spec-kit:
- Falls back to attune's native specification skill
- Provides similar structured approach
- Documents requirements systematically

## Workflow

```bash
# 1. Invoke specification skill
Skill(attune:project-specification)

# 2. Transform brief into structured spec:
#    - Functional requirements
#    - Non-functional requirements
#    - Acceptance criteria
#    - Technical constraints
#    - Dependencies

# 3. Generate specification document
#    - Saved to docs/specification.md
#    - Includes all requirements with testability

# 4. Transition to planning
#    Next: /attune:plan (use spec as input)
```

## Specification Structure

### Section 1: Overview

- **Purpose**: What this project achieves
- **Scope**: What's included and excluded
- **Stakeholders**: Who cares about this project

### Section 2: Functional Requirements

Format per requirement:
```markdown
### FR-001: [Requirement Name]

**Description**: Clear description of the requirement

**Acceptance Criteria**:
- [ ] Given [context], when [action], then [expected result]
- [ ] Given [context], when [action], then [expected result]

**Priority**: High | Medium | Low
**Dependencies**: FR-002, FR-005
**Estimated Effort**: S | M | L | XL
```

### Section 3: Non-Functional Requirements

Categories:
- **Performance**: Response times, throughput, resource usage
- **Security**: Authentication, authorization, data protection
- **Reliability**: Uptime, error handling, recovery
- **Usability**: UX requirements, accessibility
- **Maintainability**: Code quality, documentation, testing

### Section 4: Technical Constraints

- **Technology stack**: Languages, frameworks, tools
- **Integration points**: External systems, APIs
- **Data requirements**: Storage, schema, migrations
- **Deployment**: Environment, CI/CD, hosting

### Section 5: Out of Scope

Explicitly document what's NOT included to prevent scope creep.

## Arguments

- `--input <path>` - Input brief file (default: docs/project-brief.md)
- `--output <path>` - Output spec file (default: docs/specification.md)
- `--feature <name>` - Specify single feature instead of full project
- `--clarify` - Run clarification phase (like spec-kit clarify)

## Examples

### Example 1: Full Project Specification

```bash
/attune:brainstorm --domain "web application"
/attune:specify
```

**Output**: `docs/specification.md`

```markdown
# Technical Debt Tracker - Specification

## Overview

**Purpose**: Provide systematic technical debt tracking integrated with GitHub

**Scope**:
- IN: GitHub issue integration, debt prioritization, reporting
- OUT: Multi-platform support, custom integrations, AI recommendations

**Stakeholders**:
- Development teams (primary users)
- Tech leads (debt review and prioritization)
- Engineering managers (reporting and metrics)

## Functional Requirements

### FR-001: GitHub Issue Discovery

**Description**: Automatically discover and categorize technical debt from GitHub issues

**Acceptance Criteria**:
- [ ] Given a repository with issues, when scanning is triggered, then all issues with `tech-debt` label are imported
- [ ] Given imported issues, when categorizing, then each is assigned a debt type (code quality, architecture, security, performance)
- [ ] Given categorized issues, when displaying, then issues are grouped by type and priority

**Priority**: High
**Dependencies**: None
**Estimated Effort**: M

### FR-002: Debt Prioritization Framework

**Description**: Calculate priority score for each debt item based on impact and effort

**Acceptance Criteria**:
- [ ] Given a debt item, when calculating priority, then score = (impact × urgency) / effort
- [ ] Given priority scores, when displaying, then items are ranked highest to lowest
- [ ] Given a debt item, when impact/effort changes, then priority recalculates automatically

**Priority**: High
**Dependencies**: FR-001
**Estimated Effort**: M

### FR-003: Interactive Dashboard

**Description**: Web dashboard showing debt overview and trends

**Acceptance Criteria**:
- [ ] Given authenticated user, when accessing dashboard, then see total debt count and trend
- [ ] Given dashboard view, when filtering, then can filter by type, priority, age
- [ ] Given dashboard view, when clicking item, then navigate to GitHub issue

**Priority**: Medium
**Dependencies**: FR-001, FR-002
**Estimated Effort**: L

## Non-Functional Requirements

### NFR-001: Performance

- Load dashboard in < 2 seconds for repos with < 1000 issues
- Sync with GitHub every 15 minutes
- Support concurrent access by 10+ users

### NFR-002: Security

- OAuth GitHub authentication required
- Read-only access to GitHub repositories
- No data persistence of sensitive information

### NFR-003: Reliability

- 99% uptime during business hours
- Graceful degradation if GitHub API unavailable
- Error logging and monitoring

## Technical Constraints

**Stack**:
- Backend: Python 3.10+ with FastAPI
- Frontend: React 18+ with TypeScript
- Database: PostgreSQL 14+
- Deployment: Docker containers on cloud platform

**GitHub Integration**:
- GitHub App with webhook subscriptions
- REST API for issue queries
- OAuth for user authentication

## Out of Scope (v1.0)

- Multi-platform support (GitLab, Bitbucket)
- AI-powered recommendations
- Custom integration plugins
- Mobile application
- Jira synchronization

## Acceptance Testing

Each FR must have:
1. Automated unit tests
2. Integration tests
3. End-to-end test scenario

## Success Criteria

Project is successful when:
- [ ] All High priority FRs implemented and tested
- [ ] Dashboard loads in < 2 seconds
- [ ] Successfully deployed to production
- [ ] 5+ teams actively using the tool
- [ ] 90%+ user satisfaction score
```

### Example 2: Single Feature Specification

```bash
/attune:specify --feature "user authentication"
```

Creates feature-specific specification in `docs/specs/feature-user-authentication.md`

### Example 3: Clarification Phase

```bash
/attune:specify --clarify
```

Runs clarification questions (like spec-kit):
```
📋 Specification Clarification

Reviewing docs/specification.md...

Questions to resolve ambiguities:

1. FR-001: What happens if issue has no tech-debt label but mentions "debt" in description?
   → [Need clarification]

2. NFR-001: Does "< 2 seconds" include initial authentication or subsequent loads?
   → [Need clarification]

3. Technical Constraints: Which cloud platform? AWS, GCP, Azure?
   → [Need clarification]
```

## Output Format

Specification follows this template:

```markdown
# [Project Name] - Specification v[version]

**Author**: [Name]
**Date**: [YYYY-MM-DD]
**Status**: Draft | Review | Approved | Implemented

## Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1.0 | 2026-01-02 | Alex | Initial draft |

## Overview
[Purpose, scope, stakeholders]

## Functional Requirements
[FR-XXX sections with acceptance criteria]

## Non-Functional Requirements
[NFR-XXX sections with measurable targets]

## Technical Constraints
[Technology, integration, deployment requirements]

## Out of Scope
[Explicitly excluded features]

## Dependencies
[External dependencies, third-party services]

## Acceptance Testing Strategy
[How requirements will be validated]

## Success Criteria
[Measurable project success indicators]

## Glossary
[Domain-specific terms and definitions]

## References
[Related documents, prior art, research]
```

## Integration with Full Cycle

```
/attune:brainstorm    ← Generate project brief
      ↓
/attune:specify       ← You are here
      ↓
/attune:plan          ← Plan architecture
      ↓
/attune:init          ← Initialize project
      ↓
/attune:execute       ← Implement systematically
```

## Quality Checks

The specification skill automatically validates:
- ✅ All requirements have acceptance criteria
- ✅ Acceptance criteria are testable (Given-When-Then format)
- ✅ No ambiguous language ("might", "could", "maybe")
- ✅ Dependencies are documented
- ✅ Effort estimates provided
- ✅ Out of scope explicitly stated

## Related Commands

- `/attune:brainstorm` - Generate project brief
- `/attune:plan` - Create implementation plan from spec
- `/speckit-specify` - Spec-kit's specification workflow (if available)
- `/speckit-clarify` - Spec-kit's clarification workflow (if available)

## Related Skills

- `Skill(attune:project-specification)` - Specification methodology
- `Skill(spec-kit:spec-writing)` - Spec-kit spec writing (if available)
- `Skill(imbue:scope-guard)` - Scope creep prevention

## Spec-Kit Integration

When spec-kit is installed, this command automatically:
- Invokes `Skill(spec-kit:spec-writing)` for specification framework
- Uses spec-kit templates and validation
- Enables `/attune:specify --clarify` mode

Check if spec-kit is available:
```bash
/plugin list | grep spec-kit
```

Install spec-kit:
```bash
/plugin install spec-kit@claude-night-market
```
