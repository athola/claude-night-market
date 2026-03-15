---
name: verify-plugin
description: Verify plugin behavioral contract history via ERC-8004 Reputation Registry
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

Query the on-chain ERC-8004 Reputation Registry for a plugin's
behavioral contract assertion history and produce a trust
assessment.

## When to Use

- Before installing a plugin from an unfamiliar source
- In CI pipelines to gate deployments on trust scores
- To audit a plugin's verification track record over time
- When evaluating whether to upgrade trust level requirements

## When NOT to Use

- The plugin is local-only and has no on-chain identity
- You are offline and cannot reach the RPC endpoint
- The ERC-8004 contracts have not been deployed yet

## Workflow

The command runs the verification script which:

1. **Parse arguments** -- plugin name, optional level and
   score threshold
2. **Query the Reputation Registry** -- fetch assertion
   records for the plugin's on-chain identity
3. **Compute pass rates** -- calculate L1/L2/L3 pass rates
   from the assertion history
4. **Produce assessment** -- return a recommendation of
   "trusted", "caution", or "untrusted" based on whether the
   target level meets the minimum score threshold

## Output

The script prints a human-readable summary:

```
Plugin: sanctum
Recommendation: trusted
Meets threshold: True

Level scores:
  L1: 98/100 (98.0% pass rate)
  L2: 47/50 (94.0% pass rate)
  L3: 18/20 (90.0% pass rate)

Recent assertions: 20 records
```

Use `--json` for machine-readable output in CI.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Plugin meets trust threshold |
| 1 | Plugin does not meet threshold |
| 2 | Error (SDK unavailable, RPC failure) |

## Examples

Verify with defaults (L1, 80% threshold):

```bash
python3 /home/alext/claude-night-market/plugins/leyline/scripts/verify_plugin.py sanctum
```

Strict L3 verification:

```bash
python3 /home/alext/claude-night-market/plugins/leyline/scripts/verify_plugin.py sanctum --level L3 --min-score 0.9
```

JSON output for CI:

```bash
python3 /home/alext/claude-night-market/plugins/leyline/scripts/verify_plugin.py sanctum --json
```

## Prerequisites

- The `web3` package must be installed for on-chain queries
- Environment variables for RPC endpoint and contract
  addresses should be configured (see
  `leyline.erc8004.config` for defaults)
- Without web3, the script reports "unknown" with a helpful
  install message

## Notes

- All RPC calls are read-only; no wallet or private key is
  needed for verification
- Assertion history is truncated to the 20 most recent
  records in the output
- The caution zone sits between 70% and 100% of the
  threshold (e.g., for 0.8 threshold, 0.56-0.79 is caution)
