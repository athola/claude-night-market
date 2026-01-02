# Cross-Cutting Concerns

## Governance and Security Structure

```
cloud-architecture/
├── governance/SKILL.md
├── security/SKILL.md
├── cost-optimization/SKILL.md
└── shared-scripts/
    ├── policy-validator.py
    ├── security-scanner.sh
    └── cost-analyzer.py
```

## Governance Module
- Policy validation across providers
- Compliance checking for regulated industries
- Audit trail and reporting

## Security Module
- Security scanning and validation
- Access control patterns
- Data protection and encryption

## Cost Optimization Module
- Multi-provider cost estimation
- Resource optimization recommendations
- Budget monitoring and alerts

## Shared Scripts

### policy-validator.py
Validates infrastructure configurations against organizational policies

### security-scanner.sh
Performs security analysis across deployed resources

### cost-analyzer.py
Provides cost optimization recommendations

## Key Benefits

1. **Governance**: Built-in compliance and policy validation
2. **Security**: Consistent security patterns across providers
3. **Cost Management**: Cost estimation and optimization
4. **Reusability**: Shared scripts work across all providers

## Quick Start
1. Implement shared scripts in `shared-scripts/` directory
2. Create cross-cutting concern modules
3. Integrate with provider-specific modules
4. Validate with detailed testing

## Integration
Works with **hierarchical-dependencies** for provider-specific governance.
