---
name: verify-plugin
description: Verify plugin behavioral contract history via GitHub Attestations (SLSA)
arguments:
  - name: plugin-name
    description: Name of the plugin to verify
    required: true
  - name: --level
    description: Minimum assertion level to check (L1, L2, L3)
    required: false
  - name: --min-score
    description: Minimum pass rate threshold (0.0-1.0, default 0.8)
    required: false
---

# Verify Plugin Trust

Query GitHub Actions workflow runs for a plugin's behavioral
contract assertion history and produce a trust assessment.
Uses GitHub's free SLSA attestation infrastructure.

## When to Use

- Before installing a plugin from an unfamiliar source
- In CI pipelines to gate deployments on trust scores
- To audit a plugin's verification track record over time
- When evaluating whether to upgrade trust level requirements

## When NOT to Use

- The plugin is local-only with no GitHub Actions history
- You are offline and cannot reach the GitHub API
- The trust-attestation workflow has not been set up yet

## Workflow

The command runs the verification script which:

1. **Parse arguments**: plugin name, optional level and
   score threshold
2. **Query GitHub API**: fetch recent workflow run results
   for the repository
3. **Compute pass rates**: calculate L1/L2/L3 pass rates
   from workflow conclusions
4. **Produce assessment**: return a recommendation of
   "trusted", "caution", or "untrusted" based on whether
   the target level meets the minimum score threshold

## Output

The script prints a human-readable summary:

```
Plugin: sanctum
Recommendation: trusted
Meets threshold: True

Level scores:
  L1: 10/10 (100.0% pass rate)
  L2: 0/0 (0.0% pass rate)
  L3: 0/0 (0.0% pass rate)

Recent assertions: 10 records
```

Use `--json` for machine-readable output in CI.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Plugin meets trust threshold |
| 1 | Plugin does not meet threshold |
| 2 | Error (gh CLI unavailable, API failure) |

## Examples

Verify with defaults (L1, 80% threshold):

```bash
python3 plugins/leyline/scripts/verify_plugin.py sanctum
```

Strict L3 verification:

```bash
python3 plugins/leyline/scripts/verify_plugin.py sanctum --level L3 --min-score 0.9
```

JSON output for CI:

```bash
python3 plugins/leyline/scripts/verify_plugin.py sanctum --json
```

## Prerequisites

- The `gh` CLI must be installed and authenticated
- Use `--repo owner/repo` to specify a different repository
  (default: athola/claude-night-market)

## Notes

- All GitHub API calls are read-only; no write permissions
  needed
- Assertion history comes from the 10 most recent completed
  workflow runs
- The caution zone sits between 70% and 100% of the
  threshold (e.g., for 0.8 threshold, 0.56-0.79 is caution)
