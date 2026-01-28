# Hierarchical Dependency Management

## Cloud Architecture Structure

```
cloud-architecture/
├── SKILL.md (hub)
├── guide.md (orchestration guide)
├── scripts/
│   ├── provider-selector.py
│   ├── compliance-checker.sh
│   └── cost-estimator.py
└── providers/
    ├── aws/SKILL.md
    │   ├── modules/
    │   │   ├── ec2/
    │   │   ├── lambda/
    │   │   └── rds/
    ├── gcp/SKILL.md
    │   ├── modules/
    │   │   ├── compute/
    │   │   ├── cloud-run/
    │   │   └── spanner/
    └── azure/SKILL.md
        ├── modules/
        │   ├── vm/
        │   ├── functions/
        │   └── cosmosdb/
```

## Key Benefits

1. **Scalability**: Easy to add new providers and patterns
2. **Maintainability**: Clear separation of concerns
3. **Flexibility**: Independent provider modules
4. **Reusability**: Shared tools and governance

## Implementation Guidelines

- Maximum 2-level dependency depth
- Provider-specific modules isolated
- Shared scripts in root `scripts/` directory
- Clear naming conventions across providers

## Quick Start
1. Define provider-specific modules
2. Create shared scripts directory
3. Implement provider-selector for intelligent routing
4. Validate with module_validator

## Integration
Use with **dynamic-loading** for context-aware module selection.
