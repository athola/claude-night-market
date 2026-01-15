# Functional Perspective

The functional perspective examines **what the system does** - its capabilities, behaviors, and completeness.

## Analysis Framework

### 1. Feature Discovery

**Goal:** Inventory all features and capabilities.

**Methods:**
```bash
# Find entry points
glob "**/commands/*.md" "**/skills/*/SKILL.md"

# Find public APIs
grep -r "def " --include="*.py" | grep -v "^_"
grep -r "export " --include="*.ts"

# Find configuration surfaces
glob "**/*.yaml" "**/*.json" "**/config.*"
```

**Output:** Feature inventory table

| Feature | Type | Entry Point | Dependencies |
|---------|------|-------------|--------------|
| /fix-pr | Command | commands/fix-pr.md | superpowers, gh |
| proof-of-work | Skill | skills/proof-of-work/ | TodoWrite |

### 2. Behavior Tracing

**Goal:** Understand how features work end-to-end.

**Methods:**
- Trace command/skill invocation paths
- Map data flow through components
- Identify transformation steps

**Questions to answer:**
1. What inputs does this feature accept?
2. What outputs does it produce?
3. What side effects does it have?
4. What error conditions can occur?

### 3. Capability Gaps

**Goal:** Identify missing or incomplete functionality.

**Gap types:**

| Type | Description | Example |
|------|-------------|---------|
| Missing | Feature doesn't exist | No undo command |
| Incomplete | Feature exists but missing cases | Error handling gaps |
| Inconsistent | Feature behavior varies | Different APIs for same task |
| Undocumented | Feature exists but not documented | Hidden options |

### 4. Integration Points

**Goal:** Map how components connect.

**Questions:**
1. What does this component depend on?
2. What depends on this component?
3. Are dependencies explicit or implicit?
4. Are interfaces stable?

## Evaluation Criteria

### Feature Completeness

| Rating | Criteria |
|--------|----------|
| Complete | All documented capabilities implemented |
| Substantial | >80% of capabilities implemented |
| Partial | 50-80% of capabilities implemented |
| Minimal | <50% of capabilities implemented |

### Behavior Correctness

| Rating | Criteria |
|--------|----------|
| Correct | Behavior matches specification |
| Mostly correct | Minor deviations |
| Partially correct | Some behaviors incorrect |
| Incorrect | Significant behavior issues |

### Integration Quality

| Rating | Criteria |
|--------|----------|
| Well-integrated | Clean interfaces, explicit dependencies |
| Integrated | Working interfaces, some implicit deps |
| Loosely integrated | Fragile interfaces |
| Poorly integrated | Broken or missing interfaces |

## Output Format

```markdown
## Functional Analysis: [Component]

### Feature Inventory

| Feature | Status | Test Coverage | Notes |
|---------|--------|---------------|-------|
| Feature A | Complete | 85% | - |
| Feature B | Partial | 40% | Missing error handling |

### Behavior Analysis

#### Feature A
- **Input:** X, Y, Z
- **Output:** Result object
- **Side effects:** File writes, API calls
- **Error handling:** Catches IOError, raises custom exceptions

#### Feature B
- **Input:** Config file path
- **Output:** Parsed config
- **Side effects:** None
- **Error handling:** INCOMPLETE - no validation

### Capability Gaps

1. **[GAP-F1]** Missing input validation
   - Location: feature_b.py:45
   - Impact: Runtime errors on malformed input
   - Recommendation: Add schema validation

2. **[GAP-F2]** Incomplete error messages
   - Location: feature_a.py:120
   - Impact: Poor debugging experience
   - Recommendation: Add context to errors

### Integration Map

```
┌─────────────┐
│  Feature A  │──depends on──▶ External API
└─────────────┘
       │
       │ calls
       ▼
┌─────────────┐
│  Feature B  │──depends on──▶ Config file
└─────────────┘
```
```

## Checklist

- [ ] All entry points identified
- [ ] Feature inventory complete
- [ ] Behaviors traced for key features
- [ ] Gaps documented with evidence
- [ ] Integration points mapped
