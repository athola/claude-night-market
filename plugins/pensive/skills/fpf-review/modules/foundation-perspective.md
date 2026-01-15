# Foundation Perspective

The foundation perspective examines **what the system is built on** - its patterns, principles, and technical debt.

## Analysis Framework

### 1. Pattern Recognition

**Goal:** Identify architectural patterns in use.

**Methods:**
```bash
# Find structural patterns
glob "**/*.py" "**/*.ts" "**/*.go"

# Look for common patterns
grep -r "class.*Factory" --include="*.py"
grep -r "interface.*Repository" --include="*.ts"
grep -r "func.*Handler" --include="*.go"

# Find dependency injection
grep -r "@inject\|@Inject\|Container" --include="*.py" --include="*.ts"
```

**Common Patterns to Identify:**

| Pattern | Signals | Context |
|---------|---------|---------|
| Factory | `*Factory`, `create_*` | Object creation |
| Repository | `*Repository`, `*Store` | Data access |
| Strategy | `*Strategy`, interface + implementations | Algorithms |
| Observer | `*Listener`, `on_*`, `emit` | Events |
| Singleton | `instance`, `get_instance` | Shared state |
| Decorator | `@wrapper`, `*Decorator` | Behavior extension |

### 2. Principle Adherence

**Goal:** Evaluate adherence to design principles.

**SOLID Analysis:**

| Principle | Check | Warning Signs |
|-----------|-------|---------------|
| **S**ingle Responsibility | One reason to change? | God classes, mixed concerns |
| **O**pen/Closed | Extend without modify? | Excessive conditionals |
| **L**iskov Substitution | Subtypes substitutable? | Type checking, isinstance |
| **I**nterface Segregation | Focused interfaces? | Unused methods, large interfaces |
| **D**ependency Inversion | Depend on abstractions? | Concrete dependencies |

**Other Principles:**

| Principle | Check | Warning Signs |
|-----------|-------|---------------|
| DRY | No repeated logic? | Copy-paste code, similar functions |
| KISS | Simplest solution? | Over-engineering, unnecessary abstraction |
| YAGNI | Only what's needed? | Unused code, speculative features |
| Composition over Inheritance | Favor composition? | Deep inheritance, fragile base classes |

### 3. Code Quality Analysis

**Goal:** Assess code health metrics.

**Metrics:**

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| Function length | < 20 lines | 20-50 lines | > 50 lines |
| Cyclomatic complexity | < 5 | 5-10 | > 10 |
| Nesting depth | < 3 | 3-4 | > 4 |
| Parameter count | < 4 | 4-6 | > 6 |
| File length | < 300 lines | 300-500 | > 500 |

**Detection:**
```bash
# Find long functions (Python)
grep -n "def " file.py | while read line; do
  # Count lines until next def or end
done

# Find complex conditionals
grep -c "if\|elif\|else" file.py
```

### 4. Technical Debt Inventory

**Goal:** Catalog and prioritize technical debt.

**Debt Types:**

| Type | Description | Example |
|------|-------------|---------|
| Intentional | Known shortcuts | "TODO: optimize later" |
| Outdated | Dependencies/patterns | Python 2 syntax |
| Bit rot | Accumulated decay | Dead code, unused imports |
| Cruft | Unnecessary complexity | Over-abstraction |

**Detection Methods:**
```bash
# Find TODOs and FIXMEs
grep -rn "TODO\|FIXME\|XXX\|HACK" --include="*.py"

# Find deprecated usage
grep -rn "@deprecated\|DeprecationWarning" --include="*.py"

# Find dead code (unused imports)
# Use ruff, flake8, or similar
ruff check --select F401 .

# Find outdated dependencies
pip list --outdated
npm outdated
```

## Evaluation Criteria

### Pattern Appropriateness

| Rating | Criteria |
|--------|----------|
| Appropriate | Pattern fits the problem well |
| Adequate | Pattern works, not optimal |
| Questionable | Pattern may cause issues |
| Inappropriate | Pattern doesn't fit, causing problems |

### Principle Adherence

| Rating | Criteria |
|--------|----------|
| Strong | Principles consistently applied |
| Moderate | Most principles followed |
| Weak | Inconsistent application |
| Absent | Principles ignored |

### Debt Severity

| Severity | Impact | Example |
|----------|--------|---------|
| Critical | Blocking future work | Coupled architecture |
| High | Slowing development | Missing tests |
| Medium | Quality degradation | Code duplication |
| Low | Minor annoyance | Style inconsistency |

## Output Format

```markdown
## Foundation Analysis: [Component]

### Pattern Analysis

| Pattern | Location | Assessment | Notes |
|---------|----------|------------|-------|
| Factory | `core/factories.py` | Appropriate | Clean implementation |
| Singleton | `config/settings.py` | Questionable | Consider DI instead |
| Observer | `events/` | Appropriate | Well-structured |

### Principle Adherence

| Principle | Rating | Evidence |
|-----------|--------|----------|
| Single Responsibility | Strong | Clear module boundaries |
| Open/Closed | Moderate | Some switch statements |
| DRY | Weak | Repeated validation logic |

### Code Quality

| Metric | Files Analyzed | Violations | Critical |
|--------|----------------|------------|----------|
| Long functions | 45 | 3 | 1 |
| High complexity | 45 | 5 | 2 |
| Deep nesting | 45 | 2 | 0 |

### Technical Debt Inventory

| ID | Type | Location | Severity | Effort | Description |
|----|------|----------|----------|--------|-------------|
| TD-01 | Intentional | `api/v1.py:45` | Medium | 2h | TODO: add pagination |
| TD-02 | Outdated | `utils/compat.py` | High | 8h | Python 3.8 compatibility shims |
| TD-03 | Cruft | `core/base.py` | Low | 1h | Unused AbstractBase class |

### Recommendations

1. **[HIGH] Refactor singleton to use dependency injection**
   - Location: `config/settings.py`
   - Impact: Improves testability
   - Effort: 4 hours

2. **[MEDIUM] Extract validation logic to shared module**
   - Location: Multiple files
   - Impact: Reduces duplication
   - Effort: 2 hours

3. **[LOW] Remove Python 3.8 compatibility code**
   - Location: `utils/compat.py`
   - Impact: Simplifies codebase
   - Effort: 1 hour (after dropping 3.8 support)
```

## Checklist

- [ ] Architectural patterns identified
- [ ] SOLID principles evaluated
- [ ] Code quality metrics gathered
- [ ] Technical debt catalogued
- [ ] Debt prioritized by severity
- [ ] Recommendations actionable
