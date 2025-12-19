# Gap Analysis Module

## Makefile Standard Taxonomy

### Target Categories and Best Practices

#### Core Development Targets (Essential)
- **help** - Self-documenting help with categorized sections
- **all** - Default target that runs essential operations
- **clean** - Remove build artifacts and temporary files
- **test** - Run test suite (delegates to specific test targets)
- **lint** - Code quality and style checks
- **format** - Code formatting with auto-fix
- **install** - Installation for production use
- **dev-install** - Development environment setup

#### Testing Targets (Expected)
- **test-unit** - Unit tests only
- **test-integration** - Integration tests
- **test-coverage** - Coverage reports (HTML + terminal)
- **coverage-check** - Coverage threshold validation
- **test-quick** - Fast tests without coverage
- **test-parallel** - Parallel test execution

#### Quality Assurance Targets (Recommended)
- **type-check** - Static type checking (mypy)
- **security** - Security vulnerability scans (bandit)
- **quality-check** - Aggregate quality checks
- **validate** - Structure and configuration validation
- **audit** - Comprehensive quality audit

#### Documentation Targets (Optional)
- **docs** - Generate documentation
- **docs-serve** - Local documentation server
- **docs-check** - Documentation validation
- **docs-clean** - Remove generated docs

#### Utility Targets (Context-dependent)
- **status** - Project overview and statistics
- **deps-update** - Update dependencies
- **deps-check** - Check for outdated dependencies
- **benchmark** - Performance benchmarks
- **profile** - Profiling analysis

#### Demo/Dogfood Targets (Plugin-specific)
- **demo-* - Demonstration workflows
- **plugin-check** - Self-validation for plugins
- **example-* - Usage examples

## Pattern Matching Rules

### Anti-Pattern Detection

#### Critical Anti-Patterns
1. **Missing Error Handling**
   ```makefile
   # Bad: No error checking
   test:
       pytest

   # Good: Explicit error handling
   test:
       @pytest -v || { echo "Tests failed"; exit 1; }
   ```

2. **Hardcoded Paths**
   ```makefile
   # Bad: Non-portable paths
   SRC_DIR := /home/user/src

   # Good: Relative or configurable paths
   SRC_DIR ?= src
   ```

3. **Silent Failures**
   ```makefile
   # Bad: Silently ignores failures
   clean:
       @rm -rf build/

   # Good: Explicit error handling
   clean:
       @echo "Cleaning..."
       @rm -rf build/ 2>/dev/null || true
   ```

#### Structural Anti-Patterns
1. **Missing .PHONY Declarations**
   ```makefile
   # Bad: Targets not declared PHONY
   clean:
       rm -rf build/

   # Good: Proper PHONY declarations
   .PHONY: clean
   clean:
       rm -rf build/
   ```

2. **Missing Help Target**
   ```makefile
   # Bad: No documentation
   # No help target

   # Good: Self-documenting help
   help: ## Show this help message
       @awk '...' $(MAKEFILE_LIST)
   ```

3. **Inconsistent Target Naming**
   ```makefile
   # Bad: Inconsistent patterns
   test_unit:
   unittest:
   test-integration:

   # Good: Consistent hyphenated naming
   test-unit:
   test-integration:
   test-coverage:
   ```

## Consistency Checks

### Cross-Makefile Validation

#### Target Consistency
- **Naming Convention**: Hyphenated names (test-unit, not test_unit)
- **Help Comments**: All targets should have `##` comments
- **Error Handling**: Consistent error message format
- **Output Formatting**: Consistent status indicators (OK/WARN)

#### Variable Patterns
- **Configurable Variables**: Use `?=` for override capability
- **Tool Detection**: Verify required tools exist
- **Directory Variables**: Centralized path configuration
- **Shell Configuration**: Consistent shell setup

#### Plugin Architecture Patterns
- **Leaf Plugins**: Self-contained operations
- **Aggregator Makefiles**: Delegate to sub-plugins
- **Shared Includes**: Reuse common patterns
- **Plugin Delegation**: `plugin-%` targets for sub-commands

### Multi-Plugin Analysis

#### Aggregator Pattern (Root Makefile)
```makefile
# Expected pattern for plugin aggregation
PLUGIN_DIRS := plugin1 plugin2 plugin3

plugin-%:
    @$(MAKE) -C $(PLUGIN_DIR) $*

test: ## Run tests across all plugins
    @for plugin in $(PLUGIN_DIRS); do \
        $(MAKE) -C $$plugin test 2>/dev/null || echo "  (test failed)"; \
    done
```

#### Leaf Plugin Pattern
```makefile
# Expected pattern for leaf plugins
include ../abstract/config/make/common.mk

SRC_DIRS ?= src tests

test: ## Run all tests
    @$(PYTEST) -v
```

## Scoring Algorithm

### Makefile Quality Assessment (0-100 points)

#### Structure Compliance (25 points)
- **Help Target** (5 points): Self-documenting with categorization
- **PHONY Declarations** (5 points): All targets properly declared
- **Target Organization** (5 points): Logical grouping and naming
- **Variable Configuration** (5 points): Configurable with `?=`
- **Shell Configuration** (5 points): Proper error handling setup

#### Content Completeness (30 points)
- **Core Targets** (10 points): help, all, clean, test, lint
- **Testing Targets** (8 points): test-unit, coverage, quick variants
- **Quality Targets** (7 points): format, type-check, security
- **Utility Targets** (5 points): status, install, deps management

#### Error Handling (20 points)
- **Explicit Error Checking** (8 points): Proper exit codes
- **Helpful Error Messages** (6 points): Actionable error output
- **Graceful Degradation** (6 points): Optional dependencies handled

#### Consistency (15 points)
- **Naming Conventions** (5 points): Hyphenated, descriptive names
- **Output Formatting** (5 points): Consistent status indicators
- **Documentation Comments** (5 points): Complete `##` comments

#### Architecture Alignment (10 points)
- **Plugin Pattern Compliance** (5 points): Leaf vs aggregator patterns
- **Shared Include Usage** (3 points): DRY compliance
- **Delegation Support** (2 points): Proper target delegation

### Quality Levels

#### Excellent (90-100)
- Complete target coverage with advanced features
- Excellent error handling and user experience
- Follows all architectural patterns
- Includes comprehensive demo/dogfood targets

#### Good (80-89)
- Strong core target coverage
- Good error handling
- Mostly consistent patterns
- Some advanced features

#### Fair (70-79)
- Basic core targets present
- Minimal error handling
- Some inconsistencies
- Limited advanced features

#### Poor (60-69)
- Missing essential targets
- Poor error handling
- Significant inconsistencies
- Anti-patterns present

#### Critical (<60)
- Missing critical targets (help, clean)
- No error handling
- Major structural issues
- Multiple anti-patterns

## Prioritized Recommendations

### Critical Issues (Immediate Action)
1. **Add Missing Help Target**
   ```makefile
   help: ## Show this help message
       @awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
   ```

2. **Add PHONY Declarations**
   ```makefile
   .PHONY: help test clean lint format install
   ```

3. **Implement Error Handling**
   ```makefile
   test:
       @pytest -v || { echo "Tests failed"; exit 1; }
   ```

### High Priority (Next Update)
1. **Standardize Target Names** (test_unit → test-unit)
2. **Add Coverage Reporting** (test-coverage target)
3. **Implement Status Target** (project overview)
4. **Add Configuration Variables** with `?=`

### Medium Priority (Future Enhancement)
1. **Add Type Checking** (type-check target)
2. **Implement Security Scanning** (security target)
3. **Add Documentation Generation** (docs target)
4. **Include Performance Benchmarks** (benchmark target)

### Low Priority (Nice to Have)
1. **Add Parallel Test Support** (test-parallel)
2. **Implement Dependency Updates** (deps-update)
3. **Add Profiling Support** (profile target)
4. **Include Mutation Testing** (mutation-test)

## Analysis Implementation

### Gap Detection Workflow

1. **Parse Makefile Structure**
   - Extract all targets and dependencies
   - Analyze variable definitions and usage
   - Check for include statements and shared patterns

2. **Classify Plugin Type**
   - **Aggregator**: Has plugin delegation targets
   - **Leaf**: Self-contained operations
   - **Hybrid**: Mixed pattern

3. **Apply Category Scoring**
   - Score each category based on presence/absence
   - Apply pattern detection for anti-patterns
   - Check consistency across targets

4. **Generate Recommendations**
   - Prioritize by impact and effort
   - Provide specific code examples
   - Reference best practice patterns

### Example Analysis Output

```markdown
## Makefile Analysis: plugins/example

### Score: 72/100 (Fair)

#### Category Breakdown:
- **Structure Compliance**: 18/25 (Missing help target)
- **Content Completeness**: 22/30 (Missing test-coverage)
- **Error Handling**: 12/20 (Limited error checking)
- **Consistency**: 15/15 (Good naming patterns)
- **Architecture Alignment**: 5/10 (Not using shared includes)

#### Critical Issues:
1. Missing help target (5 points)
2. No error handling in test target (8 points)

#### High Priority:
1. Add test-coverage target
2. Include shared Makefile patterns
3. Add status target for project overview

#### Recommendations:
```makefile
# Add to Makefile
help: ## Show this help message
    @awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

test-coverage: ## Run tests with coverage
    @pytest --cov=example --cov-report=html --cov-report=term-missing || { echo "Coverage failed"; exit 1; }
```
```

This analysis module provides intelligent gap detection specifically tailored for the claude-night-market project structure, with clear understanding of aggregator vs leaf plugin patterns and actionable recommendations for improvement.
