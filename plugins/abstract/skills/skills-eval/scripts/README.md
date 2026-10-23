# Skills-Eval Scripts

The skills-eval tools are Python scripts in `plugins/abstract/scripts/`.
This directory holds no executables. Run every command below from
`plugins/abstract`. The scripts import PyYAML. If `python3` lacks it,
prefix the command with `uv run`, which uses the plugin environment.

Each script takes one path and writes its report to stdout, or to
`--output FILE`. The `--format` flag, on the scripts that have it,
accepts `text` (the default) or `json`.

## Tools

### skills_auditor.py

Scores every skill under a directory and lists the ones that need work.

```bash
python3 scripts/skills_auditor.py skills/
python3 scripts/skills_auditor.py skills/ --format json --output audit.json
```

### compliance_checker.py

Checks skills against the frontmatter and structure rules.
`--rules-file` loads custom rules. The script exits 0 whatever it finds.
To gate on the result, use `uv run abstract-skills check skills/`, which
exits 1 on a non-compliant report.

```bash
python3 scripts/compliance_checker.py skills/
python3 scripts/compliance_checker.py skills/ --format json
```

### improvement_suggester.py

Builds an improvement plan for one skill. Pass the skill directory or its
`SKILL.md`.

```bash
python3 scripts/improvement_suggester.py skills/skills-eval
python3 scripts/improvement_suggester.py skills/skills-eval/SKILL.md --format json
```

### token_usage_tracker.py

Estimates tokens per skill against a per-skill limit (default 2000).

```bash
python3 scripts/token_usage_tracker.py skills/
python3 scripts/token_usage_tracker.py skills/ --optimal-limit 1500
```

### tool_performance_analyzer.py

Times each executable file under the directory by running it with
`--help`. Point it only at code you trust: it executes what it finds.

```bash
python3 scripts/tool_performance_analyzer.py skills/skills-eval
```

## Shared helpers

The parsing and token helpers are in the plugin package:

```python
from abstract.frontmatter import FrontmatterProcessor
from abstract.tokens import estimate_text_tokens
```

## CI example

```yaml
- name: Skill compliance
  working-directory: plugins/abstract
  run: uv run abstract-skills check skills/
```
