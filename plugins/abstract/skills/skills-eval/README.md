# Skills Evaluation

detailed skill analysis and quality improvement tools.

## Usage

Run from `plugins/abstract`. The scripts need PyYAML. Prefix a command
with `uv run` if `python3` lacks it.

```bash
# Score every skill under a directory
python3 scripts/skills_auditor.py skills/

# Improvement plan for one skill (its directory or SKILL.md)
python3 scripts/improvement_suggester.py skills/skills-eval

# Compliance gate: exits 1 on a non-compliant report
uv run abstract-skills check skills/
```

## Tools

- **skills_auditor.py**: scores and inventories skills
- **improvement_suggester.py**: improvement plan for one skill
- **compliance_checker.py**: standards report (always exits 0)
- **token_usage_tracker.py**: tokens per skill against a limit
- **tool_performance_analyzer.py**: times executables with `--help`

Flags for each are in `scripts/README.md`.

## Key Metrics

- Structure compliance
- Token efficiency
- Documentation quality
- Tool integration
- Activation reliability

## Quick Validation

```bash
make check  # Run detailed validation
```
