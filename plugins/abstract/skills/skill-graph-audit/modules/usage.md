---
name: skill-graph-audit-usage
description: CLI reference and example workflows for the skill graph audit tool.
---

# Usage Reference

## CLI Flags

```text
python3 plugins/abstract/scripts/skill_graph.py [OPTIONS]

  --plugins-root PATH    Root containing <plugin>/skills/<name>/ tree
                         (default: plugins)
  --top-n INT            Top N hubs/orchestrators to show (default: 10)
  --format {text,json}   Output format (default: text)
  --output PATH          Write to file instead of stdout
```

## Common Workflows

### Pre-release dangling-ref check

```bash
python3 plugins/abstract/scripts/skill_graph.py \
  --plugins-root plugins --format json --output /tmp/graph.json

python3 -c "
import json
report = json.load(open('/tmp/graph.json'))
bugs = report['dangling_refs']['bugs']
if bugs:
    print(f'BLOCKING: {len(bugs)} dangling refs')
    for b in bugs:
        print(f'  {b[\"source\"]} -> {b[\"target\"]}')
    raise SystemExit(1)
print('OK: 0 internal dangling references')
"
```

### Find consolidation candidates

Hubs with >5 inbound references are core API; orchestrators with
>5 outbound references are coordination points. The intersection
(hub AND orchestrator) is the federation backbone.

```bash
python3 plugins/abstract/scripts/skill_graph.py --top-n 20 \
  | tee /tmp/graph.txt
```

### Update composition documentation

Generate the federation table for `docs/quality-gates.md` from
report JSON instead of curating manually.

## Updating External Plugin Allowlist

If a new external plugin is referenced (one not yet in
`KNOWN_EXTERNAL_PLUGINS`), update the constant in
`plugins/abstract/scripts/skill_graph.py` so refs to it are
classified as `external` rather than `bugs`.

## Limitations

- Detects only `Skill(plugin:name)` invocations. Free-text mentions
  in prose are not parsed.
- Self-references (a skill referencing itself) are skipped to avoid
  cycles in counts.
- Module-level `dependencies:` and `modules:` frontmatter are not
  yet treated as edges; see backlog item for planned extension.
