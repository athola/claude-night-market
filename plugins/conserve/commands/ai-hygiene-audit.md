---
name: ai-hygiene-audit
description: Audit codebase for AI-generated code quality issues (vibe coding, Tab bloat, slop)
usage: /ai-hygiene-audit [--focus git|duplication|tests|docs] [--report FILE] [--threshold SCORE]
---

# AI Hygiene Audit Command

Detect AI-specific code quality issues that traditional bloat detection misses.

## When To Use

Use this command when you need to:
- Suspected AI-generated code quality issues
- Before major releases to check for hidden debt
- Reviewing PRs with suspected AI generation
- After rapid AI-assisted development sprints

## When NOT To Use

- Quick fixes that don't need structured workflow
- Already know the specific issue - fix it directly

## Why This Exists

AI coding creates different problems than human coding:
- **2024**: First year copy > refactor in git history (GitClear)
- **Tab-completion bloat**: Similar code repeated instead of abstracted
- **Happy path bias**: Tests verify success, miss failures
- **Slop**: Documentation that sounds right but lacks depth

## Usage

```bash
# Full AI hygiene audit
/ai-hygiene-audit

# Focus on specific area
/ai-hygiene-audit --focus git          # Git history patterns
/ai-hygiene-audit --focus duplication  # Tab-completion bloat
/ai-hygiene-audit --focus tests        # Happy-path-only detection
/ai-hygiene-audit --focus docs         # Documentation slop

# Generate report file
/ai-hygiene-audit --report ai-hygiene-report.md

# Set pass/fail threshold (0-100)
/ai-hygiene-audit --threshold 70
```

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--focus <area>` | Limit to: `git`, `duplication`, `tests`, `docs`, `deps` | all |
| `--report <file>` | Save detailed report to file | stdout |
| `--threshold <score>` | Fail if hygiene score below threshold | none |
| `--json` | Output structured JSON for CI integration | false |

## What It Detects

### Git History Patterns
- **Massive single commits**: 500+ line additions (vibe coding signature)
- **Refactoring deficit**: <5% of commits involve refactoring
- **Churn spikes**: Code revised within 2 weeks of creation

### Duplication (Tab-Completion Bloat)
- **Repeated blocks**: 5+ line duplicates across files
- **Similar functions**: Near-identical function signatures
- **Copy-paste patterns**: Same logic with minor variations

Detection uses built-in `detect_duplicates.py` script (no external dependencies):
```bash
python3 plugins/conserve/scripts/detect_duplicates.py . --min-lines 5
python3 plugins/conserve/scripts/detect_duplicates.py . --format json --threshold 15
```

### Test Quality
- **Happy path only**: Tests without error/exception assertions
- **Test deficit**: <30% test-to-code ratio by lines
- **Trivial coverage**: Tests that verify nothing meaningful

### Documentation Slop
- **Hedge word density**: "worth noting", "arguably", "to some extent"
- **Formulaic structure**: Generic patterns without depth
- **Surface insights**: Describes WHAT without explaining WHY

### Dependency Verification
- **Hallucinated packages**: Imports for non-existent modules
- **Slopsquatting risk**: Plausible-sounding fake packages

## Example Output

```
=== AI Hygiene Audit ===
Score: 62/100 (MODERATE CONCERN)

FINDINGS:

[HIGH] Tab-Completion Bloat
  src/handlers/*.py: 4 near-identical classes
  Recommendation: Extract to shared base class
  Impact: ~2,400 duplicate tokens

[HIGH] Happy Path Tests
  tests/test_api.py: 0 error assertions in 847 lines
  Recommendation: Add pytest.raises tests

[MEDIUM] Refactoring Deficit
  2.3% of commits mention refactoring (target: >10%)
  Recommendation: Add refactoring to sprint goals

[LOW] Documentation Slop
  docs/api.md: 23 hedge phrases per 1000 words
  Recommendation: Rewrite with concrete specifics

NEXT STEPS:
  1. /unbloat --focus duplication
  2. Add error tests before new features
  3. Review massive commits for understanding gaps
```

## CI Integration

```yaml
# GitHub Actions example
- name: AI Hygiene Check
  run: |
    claude "/ai-hygiene-audit --threshold 60 --json" > hygiene.json
    if [ $(jq '.score' hygiene.json) -lt 60 ]; then
      echo "AI hygiene score below threshold"
      exit 1
    fi
```

## Relationship to Other Commands

| Command | Focus | Use Case |
|---------|-------|----------|
| `/bloat-scan` | Dead/unused code | Find DELETE candidates |
| `/ai-hygiene-audit` | AI-specific issues | Find REFACTOR candidates |
| `/unbloat` | Remediation | Fix findings from both |

**Workflow:**
```bash
/bloat-scan --level 2              # Traditional bloat
/ai-hygiene-audit                  # AI-specific issues
/unbloat                           # Address both
```

## See Also

- `ai-hygiene-auditor` agent - Implementation details
- `@module:ai-generated-bloat` - Detection patterns
- `imbue:scope-guard/anti-overengineering` - Agent psychosis warnings
- Knowledge corpus: `agent-psychosis-codebase-hygiene.md`
