# Phase 3: Meta-Evaluation Check

Run meta-evaluation on evaluation-related skills to validate recursive quality.

## Step 1: Run Meta-Evaluation

```bash
python3 plugins/sanctum/scripts/meta_evaluation.py --plugins-root plugins/
python3 plugins/sanctum/scripts/meta_evaluation.py --plugins-root plugins/ --plugin abstract
```

What It Checks:
- Recursive Quality: Evaluation skills meet their own quality standards
- TOC Requirements: Long modules (>100 lines) have Table of Contents
- Verification Steps: Code examples include verification commands
- Anti-Cargo Cult: Documentation warns against testing theater
- Test Coverage: Critical evaluation skills have BDD test validation

## Step 2: Review Report

Reports by severity (Critical, High, Medium, Low) with pass rate statistics.

## Step 3: Create Action Items

For critical and high priority issues, create TodoWrite items and recommend fixes. Use `--skip-meta-eval` to skip.
