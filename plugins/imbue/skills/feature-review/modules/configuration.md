# Configuration

Feature-review uses opinionated defaults but allows
project-specific customization through a YAML
configuration file.

## Configuration File Location

Create `.feature-review.yaml` in your project root:

```
project/
├── .feature-review.yaml    # Configuration file
├── src/
└── ...
```

## Full Configuration Schema

```yaml
# .feature-review.yaml
# All values shown are defaults - only specify what you want to change

version: 1  # Schema version (required if file exists)

weights:
  value:
    reach: 0.25              # How many users affected
    impact: 0.30             # How much improvement per user
    business_value: 0.25     # OKR/strategic alignment
    time_criticality: 0.20   # Cost of delay
  cost:
    effort: 0.40             # Development time
    risk: 0.30               # Uncertainty/unknowns
    complexity: 0.30         # Technical difficulty

thresholds:
  high_priority: 2.5         # Score > 2.5 = implement soon
  medium_priority: 1.5       # Score > 1.5 = roadmap candidate
  confidence_warning: 0.5    # Scores below this get flagged

classification:
  default_type: reactive     # proactive | reactive
  default_data: static       # static | dynamic
  patterns:
    proactive_patterns: ["*auto*", "*suggest*", "*predict*", "*prefetch*"]
    dynamic_patterns: ["*session*", "*realtime*", "*live*", "*stream*"]

tradeoffs:
  quality: 1.0               # Correctness of results
  latency: 1.0               # Response time
  token_usage: 1.0           # Context efficiency (LLM-specific)
  resource_usage: 0.8        # CPU/memory consumption
  redundancy: 0.5            # Fault tolerance
  readability: 1.0           # Code maintainability
  scalability: 0.8           # Growth handling
  integration: 1.0           # Ecosystem fit
  api_surface: 1.0           # Contract stability

github:
  enabled: true
  auto_label: true
  label_prefix: "priority/"
  default_labels: [enhancement, feature-review]
  priority_labels:
    high: "priority/high"
    medium: "priority/medium"
    low: "priority/low"

inventory:
  scan_paths: ["commands/", "skills/", "agents/", "src/"]
  exclude_patterns: ["**/test*", "**/mock*", "**/__pycache__/**"]

output:
  format: markdown           # markdown | json | yaml
  include_rationale: true
  include_tradeoffs: true
  max_suggestions: 10

backlog:
  max_items: 25              # Maximum items (guardrail, cannot exceed 25)
  stale_days: 30
  auto_archive: false
  file: "docs/backlog/feature-queue.md"
```

## Minimal Configuration Examples

### Startup (Move Fast)

```yaml
version: 1
thresholds:
  high_priority: 2.0
  medium_priority: 1.0
tradeoffs:
  redundancy: 0.3
  scalability: 0.5
backlog:
  max_items: 15
```

### Enterprise (Stability First)

```yaml
version: 1
thresholds:
  high_priority: 3.0
  confidence_warning: 0.7
tradeoffs:
  api_surface: 1.5
  redundancy: 1.2
  readability: 1.2
```

## Project-Type Templates

Adjust tradeoff weights based on project type:

| Project Type | Key Weight Adjustments |
|-------------|----------------------|
| LLM/AI Plugin | `token_usage: 1.4`, `integration: 1.3`, `api_surface: 1.3` |
| SaaS Product | `quality: 1.3`, `redundancy: 1.2`, `scalability: 1.3` |
| Internal Tool | `latency: 1.3`, `integration: 1.3`, `redundancy: 0.5` |
| Mobile App | `latency: 1.4`, `resource_usage: 1.3`, `quality: 1.3` |

## Guardrails (Always Enforced)

These rules apply regardless of configuration:

| Guardrail | Rule |
|-----------|------|
| Minimum dimensions | At least 5 tradeoff dimensions must have non-zero weight |
| Weight sum | Weights within each category must sum to 1.0 (within 0.01) |
| Confidence | Features below `confidence_warning` are always flagged |
| Breaking changes | API surface changes require explicit acknowledgment |
| Backlog limit | Maximum 25 items (forces prioritization decisions) |

## Environment Variable Overrides

Pattern: `FEATURE_REVIEW_` + uppercase path with
underscores.

```bash
FEATURE_REVIEW_HIGH_PRIORITY=3.0
FEATURE_REVIEW_GITHUB_ENABLED=false
FEATURE_REVIEW_OUTPUT_FORMAT=json
```

## Configuration Validation

```bash
/feature-review --validate-config
```

## Inheritance and Overrides

### Directory-Level Config

Child configs inherit from parent and override specific
values:

```
project/
├── .feature-review.yaml           # Project defaults
├── plugins/
│   └── .feature-review.yaml       # Plugin-specific overrides
└── experimental/
    └── .feature-review.yaml       # Experimental area config
```

### Command-Line Overrides

```bash
/feature-review --threshold.high_priority=3.0
/feature-review --weights.value.impact=0.4
/feature-review --github.enabled=false
```

## Migration Guide

### From No Configuration

1. Run `/feature-review` with defaults
2. Review output for misaligned priorities
3. Create minimal `.feature-review.yaml` with only
   changed values

### From Other Frameworks

| Framework | Mapping Strategy |
|-----------|-----------------|
| RICE | Set `reach: 0.35`, `impact: 0.35`, `effort: 0.70` (cost) |
| MoSCoW | Map to thresholds: Must (3.0), Should (2.0), Could (1.0-2.0) |

## Research Enrichment

Configure external research via the tome plugin.
When enabled, research findings adjust scoring factors
with evidence-backed deltas.

```yaml
research:
  enabled: true
  channels:
    code_search: true          # GitHub code search
    discourse: true            # HN, Reddit, Lobsters
    papers: true               # arXiv, Semantic Scholar
    triz: true                 # Cross-domain analogical reasoning
  evidence_threshold: 0.3      # Minimum evidence to apply delta
  max_delta: 2                 # Max Fibonacci steps adjustment
  timeout_seconds: 120
```

| Channel | Speed | Best For |
|---------|-------|----------|
| code_search | Fast | Measuring ecosystem adoption |
| discourse | Medium | Gauging community demand |
| papers | Slow | Academic validation |
| triz | Slow | Cross-domain innovation |

When the tome plugin is not installed, `--research` prints
a warning and proceeds with initial scores unchanged.

## Advanced Patterns

### Custom Scoring Dimensions

```yaml
custom_dimensions:
  regulatory_compliance:
    weight: 1.5
    description: "Meets GDPR/SOC2/HIPAA requirements"
    scoring: {5: "Fully compliant", 3: "Minor gaps", 1: "Concerns"}
```

### Conditional Configuration

Override weights based on feature classification:

```yaml
conditional:
  proactive:
    tradeoffs:
      latency: 0.6
      resource_usage: 1.2
  dynamic:
    tradeoffs:
      redundancy: 1.2
      scalability: 1.2
```
