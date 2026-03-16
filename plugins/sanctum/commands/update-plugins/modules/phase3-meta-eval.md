# Phase 3: Meta-Evaluation Check

Run meta-evaluation on evaluation-related skills to validate
recursive quality.

## Step 1: Run Meta-Evaluation

```bash
# Run on all evaluation skills
python3 plugins/sanctum/scripts/meta_evaluation.py --plugins-root plugins/

# Run on specific plugin
python3 plugins/sanctum/scripts/meta_evaluation.py --plugins-root plugins/ --plugin abstract

# Verbose mode for detailed output
python3 plugins/sanctum/scripts/meta_evaluation.py --plugins-root plugins/ --verbose
```

What it checks:

- Recursive Quality: Evaluation skills meet their own
  quality standards
- TOC Requirements: Long modules (>100 lines) have Table
  of Contents
- Verification Steps: Code examples include verification
  commands
- Concrete Quick Starts: Commands instead of abstract
  descriptions
- Anti-Cargo Cult: Documentation warns against testing
  theater
- Test Coverage: Critical evaluation skills have BDD test
  validation

Skills evaluated:

- abstract: skills-eval, hooks-eval, modular-skills
- imbue: proof-of-work, evidence-logging
- leyline: evaluation-framework, testing-quality-standards
- pensive: review-core, test-review, api-review,
  architecture-review
- sanctum: pr-review, test-updates
- parseltongue: python-testing
- conserve: code-quality-principles

## Step 2: Review Report

The script reports by severity and pass rate:

```
By Severity:
  Critical: X  - Skills missing or broken
  High: X      - Quality standards not met
  Medium: X    - Navigation/documentation issues
  Low: X       - Anti-cargo-cult documentation missing

Pass Rate:
  Skills Evaluated: X
  Skills Passed: X (Y%)
  Skills with Issues: X
```

## Step 3: Create Action Items

For critical and high priority issues:

1. Create TodoWrite items for tracking:
   ```
   meta-eval:<plugin>:<skill>-<issue-type>
   ```

2. Recommend fixes based on issue type:
   - Missing TOC: Add Table of Contents after frontmatter
   - Missing verification: Add "Run `command`" after examples
   - Abstract Quick Start: Replace with concrete commands
   - Missing tests: Create BDD test file

To skip meta-evaluation: use `--skip-meta-eval` flag.
