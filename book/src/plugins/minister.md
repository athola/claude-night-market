# minister

GitHub initiative tracking and release management.

## Overview

Minister helps you track project initiatives, monitor release readiness, and generate stakeholder reports. It bridges the gap between development work and project management.

## Installation

```bash
/plugin install minister@claude-night-market
```

## Skills

| Skill | Description | When to Use |
|-------|-------------|-------------|
| `github-initiative-pulse` | Initiative progress tracking | Weekly status reports |
| `release-health-gates` | Release readiness checks | Before releasing |

## Scripts

| Script | Description |
|--------|-------------|
| `tracker.py` | CLI for initiative database and reporting |

## Usage Examples

### Initiative Tracking

```bash
Skill(minister:github-initiative-pulse)

# Generates:
# - Issue completion rates
# - Milestone progress
# - Velocity trends
# - Risk flags
```

### Release Readiness

```bash
Skill(minister:release-health-gates)

# Checks:
# - CI status
# - Documentation completeness
# - Breaking change inventory
# - Risk assessment
```

### CLI Usage

```bash
# List initiatives
python tracker.py list

# Show initiative details
python tracker.py show auth-v2

# Generate weekly report
python tracker.py report --week

# Update status
python tracker.py update auth-v2 --status in-progress
```

## Initiative Structure

Initiatives track work across issues and PRs:

```yaml
initiative:
  id: auth-v2
  title: "Authentication v2"
  status: in-progress
  milestones:
    - name: "OAuth Setup"
      due: 2025-01-30
      issues: [#42, #43, #44]
    - name: "Session Management"
      due: 2025-02-15
      issues: [#45, #46]
  metrics:
    velocity: 3.5 issues/week
    completion: 65%
    risk: low
```

## Health Gates

Release health gates verify readiness:

| Gate | Checks |
|------|--------|
| **CI** | All checks passing, no flaky tests |
| **Docs** | README updated, CHANGELOG complete |
| **Breaking** | Breaking changes documented |
| **Security** | No critical vulnerabilities |
| **Coverage** | Test coverage above threshold |

### Gate Output

```markdown
## Release Health: v2.0.0

### CI Status: PASS
- All 156 tests passing
- Build time: 3m 42s
- No flaky tests detected

### Documentation: PASS
- README updated
- CHANGELOG has v2.0.0 section
- API docs generated

### Breaking Changes: WARN
- 2 breaking changes identified
- Migration guide needed for UserService API

### Security: PASS
- No critical/high vulnerabilities
- Dependencies up to date

### Coverage: PASS
- 87% coverage (threshold: 80%)

## Recommendation: CONDITIONAL RELEASE
Address breaking change documentation before release.
```

## Reporting

### Weekly Report

```bash
python tracker.py report --week

# Outputs:
# - Initiatives summary
# - This week's completions
# - Next week's focus
# - Blockers and risks
```

### Stakeholder Summary

```bash
python tracker.py report --stakeholder

# Generates executive summary:
# - High-level progress
# - Key achievements
# - Timeline updates
# - Resource needs
```

## Integration with GitHub

Minister reads from GitHub:

```bash
# Sync initiative from GitHub milestone
python tracker.py sync --milestone "v2.0"

# Pull issue status
python tracker.py refresh auth-v2
```

## Superpowers Integration

| Skill | Enhancement |
|-------|-------------|
| `issue-management` | Uses `systematic-debugging` for investigation |

## Configuration

### tracker.yaml

```yaml
github:
  repo: athola/my-project
  token_env: GITHUB_TOKEN

initiatives_dir: .minister/initiatives
reports_dir: .minister/reports

health_gates:
  coverage_threshold: 80
  max_critical_vulns: 0
  require_changelog: true
```

## Workflow Examples

### Sprint Planning

```bash
# Check initiative status
python tracker.py list

# Update priorities
python tracker.py update auth-v2 --priority high

# Generate planning report
python tracker.py report --planning
```

### Release Preparation

```bash
# Run health gates
Skill(minister:release-health-gates)

# Address any failures
# Then re-run until all pass

# Tag release
git tag v2.0.0
```

### Weekly Standup

```bash
# Generate pulse report
Skill(minister:github-initiative-pulse)

# Share with team
# Update tracker based on discussion
```

## Related Plugins

- **sanctum**: PR preparation integrates with release workflow
- **imbue**: Feature review complements initiative tracking
