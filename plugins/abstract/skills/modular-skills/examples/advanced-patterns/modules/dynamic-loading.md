# Dynamic Module Loading

## Intelligent Module Selection

The hub skill uses context-aware module loading based on user requirements:

```yaml
---
name: cloud-architecture
description: Multi-cloud architecture design and deployment
category: infrastructure
tags: [cloud, architecture, aws, gcp, azure]
dependencies:
  - governance
  - security
  - cost-optimization
conditional_dependencies:
  aws: [aws-infrastructure]
  gcp: [gcp-infrastructure]
  azure: [azure-infrastructure]
tools: [provider-selector, compliance-checker, cost-estimator]
---
```

## Provider Selection Logic

```python
# Example: scripts/provider-selector.py
def select_provider(context):
    """Intelligently select cloud provider based on context"""
    if context.get('compliance_level') == 'government':
        return 'aws'  # GovCloud support
    elif context.get('workload_type') == 'ml':
        return 'gcp'  # ML capabilities
    elif context.get('existing_ms') == True:
        return 'azure'  # Microsoft integration
    else:
        return analyze_cost_performance(context)
```

## Progressive Disclosure Implementation

**Level 1: Quick Decision Making**
```markdown
## Quick Start
1. `provider-selector` - Choose optimal cloud provider
2. `compliance-checker` - Validate governance requirements
3. `cost-estimator` - Estimate deployment costs
```

**Level 2: Provider-Specific Guidance**
```markdown
## Provider Selection
- AWS: Best for enterprise workloads
- GCP: Optimal for data/ML workloads
- Azure: Ideal for hybrid scenarios
```

**Level 3: Detailed Implementation**
See provider-specific modules for step-by-step workflows

**Level 4: Executable Scripts**
Automated scripts in `scripts/` directory

## Smart Dependency Resolution

The skill automatically:
- Analyzes current context (existing infrastructure, compliance requirements)
- Loads only necessary provider modules
- Resolves conflicts between providers
- Provides default options

## Token Optimization Strategies

- **Lazy Loading**: Load provider modules only when needed
- **Caching**: Cache expensive analyses across sessions
- **Compression**: Use shared tools instead of duplicating code
- **Context Pruning**: Remove irrelevant content based on user needs

## Key Benefits

1. **Flexibility**: Dynamic module loading based on context
2. **Efficiency**: Token optimization through intelligent loading
3. **Adaptability**: Responds to user requirements automatically

## Quick Start
1. Implement provider-selector logic
2. Configure conditional dependencies
3. Set up progressive disclosure levels
4. Test context-aware loading

## Integration
Requires **hierarchical-dependencies** for provider structure and **cross-cutting-concerns** for governance.