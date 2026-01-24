---
name: skills-eval
description: |
  Evaluate and improve Claude skill quality through auditing.
  Triggers: quality-assurance, skills, optimization, tool-use, performance-metrics, skill audit, quality review, compliance check, improvement suggestions, token usage analysis, skill evaluation, skill assessment, skill optimization, skill standards, skill metrics, skill performance.
  Use when reviewing skill quality, preparing skills for production, or auditing existing skills.
  Do not use when creating new skills (use modular-skills) or writing prose (use writing-clearly-and-concisely).
  Use this skill before shipping any skill to production.
version: 1.3.4
category: skill-management
tags: [evaluation, improvement, skills, optimization, quality-assurance, tool-use, performance-metrics]
dependencies: [modular-skills, performance-optimization]
tools: [skills-auditor, improvement-suggester, compliance-checker, tool-performance-analyzer, token-usage-tracker]
provides:
  infrastructure: ["evaluation-framework", "quality-assurance", "improvement-planning"]
  patterns: ["skill-analysis", "token-optimization", "modular-design"]
  sdk_features:
    - "agent-sdk-compatibility"
    - "advanced-metrics"
    - "dynamic-discovery"
estimated_tokens: 1800
usage_patterns:
  - skill-audit
  - quality-assessment
  - improvement-planning
  - skills-inventory
  - tool-performance-evaluation
  - dynamic-discovery-optimization
  - advanced-tool-use-analysis
  - programmatic-calling-efficiency
  - context-preservation-quality
  - token-efficiency-optimization
  - modular-architecture-validation
  - integration-testing
  - compliance-reporting
  - performance-benchmarking
complexity: advanced
evaluation_criteria:
  structure_compliance: 25     # Modular architecture, progressive disclosure
  metadata_quality: 20         # Complete frontmatter, clear descriptions
  token_efficiency: 25         # Context optimization, response compression
  tool_integration: 20         # Tool effectiveness, error handling, performance
  claude_sdk_compliance: 10    # API compatibility, best practices adherence
---
## Table of Contents

- [Overview](#overview)
- [What It Is](#what-it-is)
- [Quick Start](#quick-start)
- [Evaluation Workflow](#evaluation-workflow)
- [Evaluation and Optimization](#evaluation-and-optimization)
- [Resources](#resources)


# Skills Evaluation and Improvement

## Overview

This framework audits Claude skills against quality standards to optimize performance and reduce token waste. We use automated tools to analyze skill structure, measure context usage, and identify specific improvements.

The `skills-auditor` provides structural analysis, while the `improvement-suggester` ranks fixes by impact. Compliance is verified through the `compliance-checker`, and runtime efficiency is monitored by `tool-performance-analyzer` and `token-usage-tracker`.

## What It Is

Evaluates and improves existing skills by running quality assessments, performance analysis, and generating improvement plans.

## Quick Start

### Basic Audit
Run a full audit of all skills or target a specific file to identify structural issues.
```bash
# Audit all skills
make audit-all

# Audit specific skill
python scripts/skills_eval/skills_auditor.py --skill-path path/to/skill/SKILL.md
```

### Analysis and Optimization
Use `skill_analyzer.py` for complexity checks and `token_estimator.py` to verify the context budget.
```bash
make analyze-skill PATH=path/to/skill/SKILL.md
make estimate-tokens PATH=path/to/skill/SKILL.md
```

### Improvements
Generate a prioritized plan and verify standards compliance using `improvement_suggester.py` and `compliance_checker.py`.
```bash
make improve-skill PATH=path/to/skill/SKILL.md
make check-compliance PATH=path/to/skill/SKILL.md
```

## Evaluation Workflow

Start with `make audit-all` to inventory skills and identify high-priority targets. For each skill requiring attention, run deep analysis with `analyze-skill` to map complexity. Generate an improvement plan, apply fixes, and then run `check-compliance` to ensure the skill meets project standards. Finalize by checking the token budget to ensure long-term efficiency.

## Evaluation and Optimization

Quality assessments use the `skills-auditor` and `improvement-suggester` to generate detailed reports. Performance analysis focuses on token efficiency through the `token-usage-tracker` and tool performance via `tool-performance-analyzer`. For standards compliance, the `compliance-checker` can automate common fixes for structural issues.

### Scoring and Prioritization

We evaluate skills across five dimensions: structure compliance, content quality, token efficiency, activation reliability, and tool integration. Scores above 90 represent production-ready skills, while scores below 50 indicate critical issues that require immediate attention.

Improvements are prioritized by impact. **Critical** issues include security vulnerabilities or broken functionality. **High** priority covers structural flaws that hinder discoverability. **Medium** and **Low** priorities focus on best practices and minor optimizations.

## Resources

### Shared Modules: Cross-Skill Patterns
- **Anti-Rationalization Patterns**: See [anti-rationalization.md](../skill-authoring/modules/anti-rationalization.md)
- **Enforcement Language**: See [enforcement-language.md](../shared-patterns/modules/workflow-patterns.md)
- **Trigger Patterns**: See [trigger-patterns.md](modules/evaluation-criteria.md)

### Skill-Specific Modules
- **Trigger Isolation Analysis**: See `modules/trigger-isolation-analysis.md`
- **Skill Authoring Best Practices**: See `modules/skill-authoring-best-practices.md`
- **Authoring Checklist**: See `modules/authoring-checklist.md`
- **Evaluation Workflows**: See `modules/evaluation-workflows.md`
- **Quality Metrics**: See `modules/quality-metrics.md`
- **Advanced Tool Use Analysis**: See `modules/advanced-tool-use-analysis.md`
- **Evaluation Framework**: See `modules/evaluation-framework.md`
- **Integration Patterns**: See `modules/integration.md`
- **Troubleshooting**: See `modules/troubleshooting.md`
- **Pressure Testing**: See `modules/pressure-testing.md`

### Tools and Automation
- **Tools**: Executable analysis utilities in `scripts/` directory.
- **Automation**: Setup and validation scripts in `scripts/automation/`.
