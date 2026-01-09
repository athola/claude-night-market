---
name: update-tests
description: Update tests using TDD/BDD principles with quality validation
usage: /update-tests [paths...]
---

# Update Tests

<identification>
triggers: update tests, test update, add tests, test coverage

use_when:
- Tests need updates after code changes
- Improving test coverage with TDD/BDD patterns
</identification>

To update tests following TDD/BDD principles with meta dogfooding, load skills in order:

1. Run `Skill(sanctum:git-workspace-review)` to capture change context and complete its `TodoWrite` items.
2. Run `Skill(test-updates)` and follow the detailed workflow:
   - **Discovery**: Analyze codebase for test gaps and changes
   - **Generation**: Create new tests using TDD principles
   - **Enhancement**: Apply BDD patterns to existing tests
   - **Validation**: Run quality assurance checks

## Workflow

### Discovery Phase
- detailed scan of codebase for test coverage gaps
- Git-based change detection for recent modifications
- Targeted analysis when specific paths provided
- Priority scoring based on impact and risk

### Test Generation
- Write failing tests first (RED phase)
- Generate scaffolding for new code
- Apply TDD discipline strictly
- Follow meta dogfooding principles

### Enhancement
- Transform basic tests to BDD style
- Add edge cases and error scenarios
- Improve test organization and clarity
- Apply consistent patterns

### Quality Validation
- Static analysis for code quality
- Dynamic test execution verification
- Coverage and mutation metrics
- Peer review checklist generation

## Usage Examples

### Full Test Suite Update
```bash
# Update entire test suite
Skill(test-updates)

# With git context
Skill(sanctum:git-workspace-review)
Skill(test-updates) --detailed
```

### Targeted Updates
```bash
# Update tests for specific module
Skill(test-updates) --target src/sanctum/agents

# Update specific test file
Skill(test-updates) --target tests/test_commit_messages.py

# Update for recent changes only
Skill(test-updates) --changes-only
```

### TDD for New Features
```bash
# Apply TDD to new code
Skill(test-updates) --tdd-only --target new_feature.py

# Generate test scaffolding
Skill(test-updates) --scaffold-only --target src/new_module/
```

## Quality Gates

Before completing, validate:
- [ ] All tests follow BDD patterns
- [ ] Coverage meets minimum standards (85% line, 80% branch)
- [ ] Mutation score is acceptable (>80%)
- [ ] Tests are independent and fast
- [ ] Documentation is clear and detailed

## Manual Execution

If skills cannot be loaded, follow these steps:

1. **Analyze Changes**
   ```bash
   git status
   git diff --name-only HEAD~1
   find src -name "*.py" -exec wc -l {} \;
   ```

2. **Run Coverage Analysis**
   ```bash
   uv run pytest --cov=src --cov-report=term-missing
   ```

3. **Apply TDD**
   - Write failing test first
   - Implement minimal code to pass
   - Refactor for clarity

4. **Add BDD Patterns**
   - Use Given/When/Then structure
   - Add descriptive test names
   - Include edge cases

5. **Validate Quality**
   ```bash
   uv run ruff check tests/
   uv run mypy tests/
   uv run pytest -v
   ```

## Integration with CI/CD

The command integrates seamlessly with CI/CD pipelines:
- Pre-commit validation
- Pull request checks
- Coverage reporting
- Quality gate enforcement

## Meta Dogfooding

This command practices what it preaches:
- Its own tests follow strict TDD
- Uses BDD patterns for behavior clarity
- Validates quality continuously
- Serves as a living example of best practices
