# Enhanced Pre-commit Hooks Infrastructure

This document describes the enhanced pre-commit hooks infrastructure with advanced governance automation for the Claude Code marketplace project.

## Overview

The enhanced pre-commit hooks provide comprehensive quality validation across multiple dimensions:
- **Performance Regression Prevention**: Detects performance degradation in skills and plugins
- **Technical Debt Detection**: Identifies and reports new technical debt patterns
- **Plugin API Compatibility**: Ensures plugin structure compliance and version compatibility
- **Context Optimization Enforcement**: Enhances existing context optimization with stricter governance
- **Quality Gate Enforcement**: Blocks merges on critical quality violations

## Hook Scripts

### 1. Performance Regression Detector (`scripts/performance_regression_detector.py`)

**Purpose**: Detects performance degradation by comparing against baseline performance metrics.

**Features**:
- File size and token count analysis
- Complexity score calculation
- Baseline comparison and regression detection
- Automatic baseline updates

**Configuration**: Configurable thresholds via command-line or `.claude/performance_baseline.json`

**Exit Codes**:
- `0`: No regressions detected
- `1`: Performance regressions found

### 2. Technical Debt Detector (`scripts/technical_debt_detector.py`)

**Purpose**: Identifies technical debt patterns and code quality issues.

**Features**:
- Python-specific analysis (long functions, complexity, bare except)
- Markdown structure validation (frontmatter, module nesting)
- Configuration file validation (hardcoded paths, environment variables)
- TODO/FIXME comment detection

**Severity Levels**:
- **Critical**: Syntax errors, missing critical structures
- **High**: Bare except, complex functions
- **Medium**: TODO comments, missing frontmatter
- **Low**: Magic numbers, style issues

**Exit Codes**:
- `0`: No critical issues
- `1`: Critical issues or too many high-severity issues

### 3. Plugin API Compatibility Checker (`scripts/plugin_api_compatibility_checker.py`)

**Purpose**: Ensures plugin structure compliance and version compatibility.

**Features**:
- Plugin structure validation (`.claude-plugin/plugin.json` requirements)
- Semantic version checking
- Dependency compatibility analysis
- Skill file compliance (frontmatter, structure)

**Validations**:
- Required fields (name, version)
- Recommended fields (description, author, license)
- Plugin directory structure
- Cross-plugin compatibility

**Exit Codes**:
- `0`: All plugins compatible
- `1`: Compatibility errors found

### 4. Enhanced Context Optimizer (`scripts/enhanced_context_optimizer.py`)

**Purpose**: Advanced context window management with governance enforcement.

**Features**:
- Progressive disclosure analysis
- Structure quality scoring
- Governance compliance checking
- Optimization recommendations

**Governance Dimensions**:
- File size limits (configurable)
- Token count limits
- Frontmatter requirements
- Modular structure validation
- Progressive disclosure requirements

**Configuration**: `.claude/context_governance.json`

**Exit Codes**:
- `0`: Within governance limits
- `1`: Critical governance violations

### 5. Quality Gate Enforcer (`scripts/quality_gate_enforcer.py`)

**Purpose**: Comprehensive quality validation across multiple dimensions.

**Features**:
- Multi-dimensional quality assessment
- Configurable blocking rules
- Critical issue aggregation
- Actionable recommendations

**Quality Dimensions**:
- **Performance**: File size, tokens, complexity
- **Security**: Hardcoded secrets, insecure functions
- **Maintainability**: Technical debt, code structure
- **Compliance**: Plugin structure, metadata

**Configuration**: `.claude/quality_gates.json`

**Exit Codes**:
- `0`: Quality gates passed
- `1`: Quality gates blocked

## Configuration

### Pre-commit Configuration

The enhanced hooks are configured in `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      # Enhanced Governance Automation Hooks
      - id: performance-regression-detector
        name: Performance Regression Detection
        entry: python3 scripts/performance_regression_detector.py
        language: system
        files: ^(plugins|scripts)/.*\.(py|md|yaml|yml|json)$
        pass_filenames: false
        args: [".", "--update-baseline"]

      - id: technical-debt-detector
        name: Technical Debt Detection
        entry: python3 scripts/technical_debt_detector.py
        language: system
        files: ^(plugins|scripts)/.*\.(py|md|yaml|yml|json)$
        pass_filenames: false
        args: ["."]

      - id: plugin-api-compatibility-checker
        name: Plugin API Compatibility Validation
        entry: python3 scripts/plugin_api_compatibility_checker.py
        language: system
        files: ^plugins/.*\.json$|^plugins/.*plugin\.yaml$|^plugins/.*plugin\.yml$
        pass_filenames: false
        args: ["."]

      - id: enhanced-context-optimizer
        name: Enhanced Context Optimization
        entry: python3 scripts/enhanced_context_optimizer.py
        language: system
        files: ^.*SKILL\.md$|^plugins/.*\.py$
        pass_filenames: false
        args: ["."]

      - id: quality-gate-enforcer
        name: Quality Gate Enforcement
        entry: python3 scripts/quality_gate_enforcer.py
        language: system
        files: ^(plugins|scripts)/.*\.(py|md|yaml|yml|json)$
        pass_filenames: false
        args: ["."]
        stages: [pre-commit, pre-merge-commit]
```

### Governance Configuration

#### Quality Gates (`.claude/quality_gates.json`)

```json
{
  "enforce_blocking": true,
  "max_critical_issues": 3,
  "max_warnings_per_dimension": 5,
  "dimensions": {
    "performance": {
      "enabled": true,
      "max_file_size_kb": 20,
      "max_tokens_per_file": 5000,
      "max_function_lines": 60,
      "max_complexity_score": 12,
      "block_on_violation": false
    },
    "security": {
      "enabled": true,
      "block_hardcoded_secrets": true,
      "block_insecure_functions": true,
      "require_input_validation": true,
      "block_on_violation": true
    },
    "maintainability": {
      "enabled": true,
      "max_technical_debt_ratio": 0.3,
      "require_code_comments": false,
      "max_nesting_depth": 5,
      "block_on_violation": false
    },
    "compliance": {
      "enabled": true,
      "require_plugin_structure": true,
      "require_proper_metadata": true,
      "block_on_violation": false
    }
  }
}
```

#### Context Governance (`.claude/context_governance.json`)

```json
{
  "enforce_strict_limits": false,
  "require_progressive_disclosure": true,
  "require_modular_structure": true,
  "require_optimization_level": "standard",
  "block_on_critical_violations": false,
  "max_violations_per_file": 5,
  "optimization_patterns": {
    "progressive_disclosure": ["overview", "basic", "advanced", "reference"],
    "modular_structure": ["modules/", "examples/", "scripts/"],
    "content_hierarchy": ["#", "##", "###", "####"]
  }
}
```

## Usage

### Installation

1. Ensure all hook scripts are executable:
   ```bash
   chmod +x scripts/*.py
   ```

2. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

### Running Hooks Manually

To run individual hooks for testing:

```bash
# Performance regression detection
python3 scripts/performance_regression_detector.py .

# Technical debt detection
python3 scripts/technical_debt_detector.py .

# Plugin compatibility check
python3 scripts/plugin_api_compatibility_checker.py .

# Context optimization
python3 scripts/enhanced_context_optimizer.py .

# Quality gate enforcement
python3 scripts/quality_gate_enforcer.py .
```

### Running All Hooks

```bash
pre-commit run --all-files
```

## Hook Output

### Performance Regression Detector

```
Performance Regression Report
============================================================
[PASS] No performance regressions detected
```

or:

```
Performance Regression Report
============================================================
171 files with performance issues:

📁 docs/architecture-analysis-report.md
   ❌ Complexity exceeds limit: 179.9 > 100.0

💡 Recommendations:
  • Consider breaking large files into smaller modules
  • Use progressive disclosure for complex skills
```

### Technical Debt Detector

```
Technical Debt Detection Report
============================================================
CRITICAL ISSUES (206):
----------------------------------------
📁 docs/api-overview.md:1
   Missing YAML frontmatter
   💡 Add proper YAML frontmatter with metadata
```

### Plugin API Compatibility Checker

```
Plugin API Compatibility Report
============================================================
ERROR ISSUES (3):
----------------------------------------
🔌 quill
   Missing .claude-plugin/plugin.json
   💡 Create plugin.json with required structure
```

### Enhanced Context Optimizer

```
Enhanced Context Optimization Report
======================================================================
Summary:
  Files analyzed: 852
  Critical violations: 880
  Warnings: 491

🚫 GOVERNANCE ENFORCEMENT: 880 critical violations detected
```

### Quality Gate Enforcer

```
Quality Gate Enforcement Report
======================================================================
Overall Status: 🚫 BLOCK
Files analyzed: 852
Total metrics: 1817

🚫 QUALITY GATE BLOCKED
Commit will be blocked due to critical quality violations.
```

## Integration with CI/CD

### GitHub Actions

Add to your workflow:

```yaml
- name: Run Quality Gates
  run: |
    python3 scripts/quality_gate_enforcer.py .
    python3 scripts/performance_regression_detector.py .
    python3 scripts/technical_debt_detector.py .
```

### Pre-push Hooks

Configure in `.pre-commit-config.yaml`:

```yaml
- id: quality-gate-enforcer
  stages: [pre-push]
```

## Troubleshooting

### Common Issues

1. **Permission Denied**: Make scripts executable with `chmod +x scripts/*.py`

2. **Python Not Found**: Ensure Python 3 is installed and accessible

3. **Missing Dependencies**: Scripts are designed to work with standard library only

4. **Git Integration**: Hooks only run on staged files by default

### Debug Mode

Run hooks with verbose output:

```bash
python3 scripts/quality_gate_enforcer.py . --verbose
```

### Configuration Issues

Validate configuration files:

```bash
python3 -m json.tool .claude/quality_gates.json
python3 -m json.tool .claude/context_governance.json
```

## Maintenance

### Updating Baselines

Performance baselines are automatically updated. To force an update:

```bash
python3 scripts/performance_regression_detector.py . --update-baseline
```

### Reviewing Violations

Regular reviews of detected violations help maintain code quality:

1. Critical violations should be addressed immediately
2. High-severity warnings should be planned for fixes
3. Medium/Low issues can be addressed during refactoring

## Performance Considerations

- Hooks only analyze changed files by default
- Caching reduces repeated analysis
- Configurable thresholds prevent false positives
- Parallel execution supported via pre-commit

## Contributing

When adding new hooks:

1. Follow the established pattern of returning clear exit codes
2. Provide comprehensive help/documentation
3. Include configuration options where appropriate
4. Test with the actual codebase
5. Update this documentation

## Security Considerations

- Hooks run with user permissions
- No network access required
- All analysis is local
- Sensitive data patterns detected but not stored
