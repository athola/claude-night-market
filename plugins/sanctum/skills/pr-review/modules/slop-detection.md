# Slop Detection Integration

## Documentation Review

For all changed `.md` files, invoke `Skill(scribe:slop-detector)`:
- Score ≥ 3.0: Flag as IN-SCOPE (should remediate)
- Score ≥ 5.0: Flag as BLOCKING if `--strict` mode

## Commit Message Review

Scan all PR commit messages for slop markers:

```bash
gh pr view <number> --json commits --jq '.commits[].messageBody' | \
  grep -iE 'leverage|seamless|comprehensive|delve|robust|utilize|facilitate'
```
If commits contain slop, add a SUGGESTION with remediation guidance.

## PR Description Review

Apply `scribe:slop-detector` to PR body:
- Tier 1 words in the description: SUGGESTION to rephrase
- Marketing phrases ("take it to the next level"): flag for removal
