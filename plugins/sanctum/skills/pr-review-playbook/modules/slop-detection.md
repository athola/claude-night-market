# Slop Detection Integration

## What a Score Means

A score decides where the reviewer reads closely. The thresholds below
pick the documents. A high score sends the reviewer to the claims: run
the cited commands, open the cited paths, and confirm the numbers. The
finding to report is the false claim. Reworded prose that keeps a false
claim is still wrong.

The signal points one way. Text gets rewritten to pass a detector, and
nobody rewrites careful text to fail one. A low score is weak evidence
that anyone checked the text.

One false claim in a high-scoring document makes hidden ones likely.
After the first, check every claim in that document rather than
sampling.

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
