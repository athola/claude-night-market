# Integration with Other Skills

## Complementary Skills

### modular-skills
- **Purpose**: Provides structural analysis and modular design patterns
- **Integration**: Uses `scripts/skill_analyzer.py` and
  `scripts/token_estimator.py`
- **Workflow**: Run structural analysis before detailed evaluation
- **Benefits**: validates proper modularization and token efficiency

```bash
# Combined workflow, run from plugins/abstract
python3 scripts/skill_analyzer.py --file skills/skills-eval/SKILL.md
python3 scripts/compliance_checker.py skills/
python3 scripts/improvement_suggester.py skills/skills-eval
```

### testing-skills
- **Purpose**: Validation and testing patterns for skills
- **Integration**: Compatible with test-driven development approaches
- **Workflow**: Use evaluation results to inform test coverage
- **Benefits**: detailed quality assurance across all dimensions

### documentation-standards
- **Purpose**: validates consistent documentation practices
- **Integration**: Aligns with documentation best practices
- **Workflow**: Use documentation evaluation as part of overall assessment
- **Benefits**: Unified documentation approach across skill ecosystem

### workflow-automation
- **Purpose**: Automates skill development and maintenance workflows
- **Integration**: Provides CI/CD patterns for skill management
- **Workflow**: Integrate evaluation into automated pipelines
- **Benefits**: Continuous quality monitoring and improvement

## Workflow Integration

### Development Pipeline
```bash
# Pre-commit gate: exits 1 on a non-compliant report
uv run abstract-skills check skills/

# Post-development analysis
python3 scripts/skills_auditor.py skills/
python3 scripts/improvement_suggester.py skills/skills-eval
```

`scripts/compliance_checker.py` reports the same findings but exits 0
whatever it finds. It cannot gate a commit.

### Continuous Integration
```yaml
# GitHub Actions steps
- name: Compliance check
  working-directory: plugins/abstract
  run: uv run abstract-skills check skills/
- name: Quality assessment
  working-directory: plugins/abstract
  run: python3 scripts/skills_auditor.py skills/ --format json
```

### Monitoring and Alerting
- **Quality Thresholds**: Set minimum acceptable scores
- **Performance Metrics**: Monitor token usage and activation rates
- **Security Scanning**: Regular compliance and security checks
- **Trend Analysis**: Track quality improvements over time

## Best Practices

### Evaluation Frequency
- **Pre-commit**: Quick compliance and security checks
- **Pre-release**: detailed evaluation and improvement planning
- **Periodic**: Quarterly full-skill inventory and assessment
- **Triggered**: After major changes or updates

### Integration Strategies
1. **Progressive Enhancement**: Start with basic evaluation, add advanced features
2. **Custom Thresholds**: Set quality gates appropriate to your context
3. **Automated Workflows**: Integrate evaluation into development pipelines
4. **Continuous Improvement**: Use evaluation results for ongoing optimization

### Tool Orchestration
- **Discovery First**: Always run skills discovery before detailed analysis
- **Prioritization**: Use improvement suggester to focus efforts
- **Validation**: Verify fixes with compliance checker
- **Monitoring**: Track quality metrics over time
