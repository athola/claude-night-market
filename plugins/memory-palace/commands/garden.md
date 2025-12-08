# Digital Garden Command

## Usage

Manage and analyze digital gardens for evolving knowledge bases.

### Calculate Metrics
```
/garden metrics <path-to-garden.json> [--format json|brief|prometheus]
```
Calculates health metrics for a digital garden.

### Check Health
```
/garden health <path-to-garden.json>
```
Provides a health assessment with maintenance recommendations.

### Seed Content
```
/garden seed <garden-path> "<title>" --section <section> --links <related>
```
Adds new content to the garden with initial links.

### Tend Garden
```
/garden tend <garden-path> --action <prune|expand|archive>
```
Performs maintenance actions on garden content.

## What It Does

1. **Tracks Metrics**: Calculates link density, freshness, maturity
2. **Assesses Health**: Identifies areas needing maintenance
3. **Seeds Content**: Adds new notes with proper linking
4. **Manages Lifecycle**: Promotes, archives, and prunes content
5. **Exports Data**: Outputs metrics in multiple formats

## Metrics Tracked

| Metric | Description | Target |
|--------|-------------|--------|
| `plots` | Total content items | - |
| `link_density` | Average links per plot | > 2.0 |
| `avg_days_since_tend` | Average staleness | < 7 days |

## Output Formats

- **json**: Full metrics as structured JSON
- **brief**: One-line summary for quick checks
- **prometheus**: Exposition format for monitoring systems

## Examples

```bash
# Calculate metrics
/garden metrics ~/my-garden.json --format brief
# Output: plots=42 link_density=3.2 avg_days_since_tend=4.5

# Check health
/garden health ~/my-garden.json

# Add new content
/garden seed ~/my-garden.json "OAuth Overview" --section auth --links "Authentication,Security"

# Prune stale content
/garden tend ~/my-garden.json --action prune
```

## Integration

Uses the garden_metrics.py tool:
```bash
python scripts/garden_metrics.py <path> [--format <format>]
```
