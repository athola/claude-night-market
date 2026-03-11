---
name: stewardship-health
description: Display stewardship health dimensions for one or all plugins
usage: /stewardship-health [plugin-name]
---

# Stewardship Health

Display the current stewardship health dimensions for Night Market
plugins. Health is shown in descriptive language, not numeric
scores or letter grades.

## Usage

```bash
# Show health summary for all plugins
/stewardship-health

# Show detailed health for a specific plugin
/stewardship-health sanctum
```

## What It Does

1. Measures six health dimensions per plugin:
   - **Documentation freshness**: when docs were last updated
   - **Test coverage**: whether coverage data is available
   - **Code quality**: presence of quality tooling
   - **Contributor friendliness**: README, stewardship section,
     examples
   - **Improvement velocity**: stewardship actions recorded
   - **Virtue practice**: count of virtue-tagged stewardship
     actions (displays "not practiced" when none exist)

2. Displays results as descriptive labels, not scores

3. Reports "not measured" for any dimension where data is
   unavailable (never shows zero or an error)

## Implementation

Invoke `Skill(leyline:stewardship)` for the five principles,
then run the health dimensions script at
`plugins/leyline/scripts/plugin_health.py`.

For each plugin, call `get_plugin_health()` with:
- `plugin_dir`: path to the plugin directory
- `actions_dir`: path to `.claude/stewardship/`
- `plugin_name`: name of the plugin

Display the results in a table for all-plugins view, or
in a detailed list for single-plugin view.

## Example Output

```
Plugin   | Docs          | Tests        | Quality          | Friendly            | Velocity   | Virtues
---------|---------------|--------------|------------------|---------------------|------------|---------------
sanctum  | updated today | not measured | pyproject, tests | README, stewardship | 3 actions  | 2 (care, diligence)
leyline  | 2 days ago    | not measured | pyproject, tests | README, stewardship | 1 action   | 1 (humility)
abstract | 5 days ago    | not measured | pyproject, tests | README, stewardship | no actions | not practiced
```

## Related

- `STEWARDSHIP.md` for the five stewardship principles
- `Skill(leyline:stewardship)` for layer-specific guidance
- `plugins/leyline/scripts/plugin_health.py` for the
  measurement implementation
