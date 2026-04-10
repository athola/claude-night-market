# Test Generation Module

## Overview

Automated test scaffolding and generation following TDD/BDD principles. Creates test templates that developers complete using proper TDD workflow.

## Capabilities

- **Generation strategies**: Code analysis, git change detection, API-based
- **Test templates**: Function, class, and API scaffolding
- **Smart features**: Parameter discovery, error scenarios, context-aware patterns
- **Content tests**: BDD templates for skill content assertions

## Workflow

1. **Analyze**: Parse code structure and dependencies
2. **Discover**: Identify test scenarios and edge cases
3. **Generate**: Create test scaffolding with BDD patterns
4. **Review**: Validate generated tests
5. **Complete**: Developer finishes with TDD cycle

## Best Practices

### Do Generate
- Test scaffolding with TODO comments
- BDD-style structure templates
- Parameterized test skeletons
- Mock/stub setup patterns

### Don't Generate
- Actual test implementations
- Complex assertions
- Business logic
- Mock behavior (too specific)

---

### Generation Strategies

Different approaches for discovering what needs testing and
generating appropriate test scaffolding.

#### From Code Analysis

Analyzes existing code to generate appropriate test scaffolding.

```python
def generate_tests_from_code(code_path):
    """Generate test scaffolding from code analysis."""

    # Parse the code
    ast_tree = ast.parse(open(code_path).read())

    # Extract testable elements
    functions = extract_functions(ast_tree)
    classes = extract_classes(ast_tree)

    # Generate test templates
    for func in functions:
        generate_function_test_template(func)

    for cls in classes:
        generate_class_test_template(cls)
```

#### From Git Changes

Generates tests for new or modified code.

```python
def generate_tests_for_changes(git_diff):
    """Generate tests based on git changes."""

    changes = parse_git_diff(git_diff)

    for change in changes:
        if change.type == 'new_function':
            generate_new_function_test(change)
        elif change.type == 'modified_signature':
            generate_updated_test(change)
        elif change.type == 'new_class':
            generate_class_test_suite(change)
```

#### From API Definitions

Generates integration tests from API contracts or OpenAPI specs.

```python
def generate_api_tests(openapi_spec):
    """Generate BDD-style API tests from OpenAPI spec."""

    for endpoint in openapi_spec.paths:
        for method in endpoint.methods:
            generate_endpoint_test(endpoint, method)
```

#### Strategy Selection

Choose based on your needs:
- **Code Analysis**: For existing code without tests
- **Git Changes**: For recent modifications
- **API Definitions**: For contract-first development

---

### Test Templates

Standard templates for different types of tests following BDD
patterns.

#### Function Test Template

```python
def test_{function_name}_{scenario}():
    """
    GIVEN {given_context}
    WHEN {when_action}
    THEN {then_expected}
    """
    # TODO: Arrange - Set up test context
    # TODO: Act - Execute the function
    # TODO: Assert - Verify the outcome
    pass
```

#### Class Test Template

```python
class Test{ClassName}:
    """BDD-style tests for {ClassName} behavior."""

    def setup_method(self):
        """Setup test instance."""
        self.instance = {ClassName}()

    @pytest.mark.bdd
    def test_{method_name}_{scenario}(self):
        """
        GIVEN {given_context}
        WHEN {when_action}
        THEN {then_expected}
        """
        # TODO: Implement test following BDD pattern
        pass

    def teardown_method(self):
        """Cleanup after each test."""
        pass
```

#### API Test Template

```python
@pytest.mark.bdd
def test_{endpoint}_{method}_{scenario}(client):
    """
    GIVEN {given_context}
    WHEN making {method} request to {endpoint}
    THEN response should be {expected_status}
    AND response should contain {expected_content}
    """
    # TODO: Setup request data
    # TODO: Make API call
    # TODO: Verify response
    pass
```

#### Using Templates

Templates provide scaffolding that developers complete using TDD:
1. Write the failing test (RED)
2. Implement minimal code to pass (GREEN)
3. Refactor for clarity (REFACTOR)

---

### Smart Features

Advanced features that make test generation more intelligent
and context-aware.

#### Parameter Discovery

```python
def discover_test_parameters(func):
    """Discover parameters for test generation."""

    params = inspect.signature(func).parameters

    test_cases = []

    # Happy path
    test_cases.append(generate_happy_path_test(params))

    # Edge cases
    for param in params:
        if param.annotation == str:
            test_cases.append(generate_string_edge_cases(param.name))
        elif param.annotation == int:
            test_cases.append(generate_numeric_edge_cases(param.name))

    return test_cases
```

#### Error Scenario Generation

```python
def generate_error_scenarios(func):
    """Generate error handling test scenarios."""

    scenarios = []

    # Type errors
    scenarios.extend(generate_type_error_tests(func))

    # Value errors
    scenarios.extend(generate_value_error_tests(func))

    # Dependency errors
    scenarios.extend(generate_dependency_error_tests(func))

    return scenarios
```

#### Context-Aware Patterns

Recognizes common patterns to generate specialized tests:
- Repository pattern
- Service pattern
- Command pattern
- Factory pattern

#### Quality-Aware Generation

Includes:
- Smart assertion generation
- Parameterized test skeletons
- Mock/stub setup patterns

---

### Content Test Templates

BDD test templates for each content assertion level. Use these
as scaffolding when generating content tests for execution
markdown files.

Reference: `leyline:testing-quality-standards/modules/content-assertion-levels.md`

#### Level 1: Keyword Presence

Minimum viable content test. Validates structural completeness.

```python
from pathlib import Path
import pytest


class TestExampleSkillContent:  # Rename to match your skill
    """Feature: example skill has required structural elements.

    As a skill interpreted by Claude Code
    I want all required sections to be present
    So that Claude has complete instructions to follow.

    Level 1: Structural presence checks.
    """

    @pytest.fixture
    def skill_path(self) -> Path:
        # Adjust "example-skill" to your actual skill directory name
        return Path(__file__).parents[3] / "skills" / "example-skill" / "SKILL.md"

    @pytest.fixture
    def skill_content(self, skill_path: Path) -> str:
        return skill_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_has_required_sections(self, skill_content: str) -> None:
        """Given the skill content
        When Claude loads it for execution
        Then all required sections must be present."""
        required = [
            "## When To Use",
            "## When NOT To Use",
            # Add skill-specific required sections
        ]
        for section in required:
            assert section in skill_content, f"Missing '{section}'"

    @pytest.mark.bdd
    @pytest.mark.unit
    @pytest.mark.parametrize("module_name", [
        # List modules referenced in SKILL.md
    ])
    def test_referenced_modules_exist(
        self, skill_path: Path, module_name: str
    ) -> None:
        """Given modules referenced in the skill
        Then each must exist on disk with content."""
        module_path = skill_path.parent / "modules" / module_name
        assert module_path.exists(), f"Referenced module {module_name} not found"
        content = module_path.read_text()
        min_lines = 10
        assert len(content.splitlines()) >= min_lines, (
            f"Module {module_name} has fewer than {min_lines} lines"
        )
```

#### Level 2: Code Example Validity

Validates embedded code examples parse correctly and have
required schema.

```python
import json
import re

# --- Level 2: Code example validity ---
# Add these methods inside your Test*Content class

@pytest.fixture
def json_code_blocks(self, skill_content: str):
    """Extract all JSON code blocks from the skill."""
    return re.findall(r"```json\n(.*?)```", skill_content, re.DOTALL)

@pytest.mark.bdd
@pytest.mark.unit
def test_all_json_examples_parse(self, json_code_blocks) -> None:
    """Given JSON code blocks in the skill
    When Claude copies them as configuration templates
    Then every block must be valid JSON."""
    assert len(json_code_blocks) > 0, "Skill should contain JSON examples"
    for i, block in enumerate(json_code_blocks):
        try:
            json.loads(block)
        except json.JSONDecodeError as exc:
            pytest.fail(f"JSON block #{i + 1} is invalid: {exc}")

@pytest.mark.bdd
@pytest.mark.unit
def test_version_references_exist(self, skill_content: str) -> None:
    """Given version references in the skill
    Then each must follow semantic versioning format."""
    versions = re.findall(r"\d+\.\d+\.\d+", skill_content)
    # Verify at least one version reference exists
    # (adjust based on whether skill uses version gates)
    assert len(versions) >= 1, "Expected at least one version reference"
```

#### Level 3: Behavioral Contracts

Validates semantic correctness, cross-references, and
anti-patterns.

```python
# --- Level 3: Behavioral contracts ---
# Add these methods inside your Test*Content class
# Requires: re (imported in Level 2), Path (imported in Level 1)

@pytest.mark.bdd
@pytest.mark.unit
def test_no_forbidden_language(self, skill_content: str) -> None:
    """Given the skill instructs Claude's behavior
    When Claude reads the instructions
    Then it must NOT find manipulative imperatives.

    Imperative language causes Claude to ignore user intent
    and force actions without consent.
    """
    forbidden = [
        "YOU MUST EXECUTE THIS NOW",
        "MANDATORY AUTO-CONTINUATION",
        # Add context-specific forbidden phrases
    ]
    for phrase in forbidden:
        assert phrase not in skill_content, (
            f"Contains manipulative language: '{phrase}'. "
            "Instructions should be informational, not imperative."
        )

@pytest.mark.bdd
@pytest.mark.unit
def test_offers_multiple_strategies(self, skill_content: str) -> None:
    """Given the skill guides Claude's decisions
    Then it must offer multiple approaches, not force one path.

    Single-path guidance removes user agency.
    """
    strategies = [
        # List expected alternative strategies
    ]
    found = [s for s in strategies if s.lower() in skill_content.lower()]
    min_strategies = 3
    assert len(found) >= min_strategies, (
        f"Too few strategies: {found}, need at least {min_strategies}"
    )

@pytest.mark.bdd
@pytest.mark.unit
def test_version_refs_cross_reference_docs(
    self, skill_content: str
) -> None:
    """Given version references in the skill
    Then each must exist in compatibility documentation.

    Prevents Claude from citing nonexistent versions.
    """
    versions = set(re.findall(r"2\.1\.(\d+)", skill_content))
    compat_dir = (
        Path(__file__).parents[4]  # Adjust depth for your test location
        / "abstract"
        / "docs"
        / "compatibility"
    )
    compat_content = ""
    for compat_file in compat_dir.glob("compatibility-features*.md"):
        compat_content += compat_file.read_text()

    for minor in versions:
        version_str = f"2.1.{minor}"
        assert version_str in compat_content, (
            f"References {version_str} but it's missing from "
            "compatibility-features*.md"
        )
```

#### Choosing the Right Level

| Observed in Git Diff | Start With |
|---|---|
| New skill or module created | L1 (sections + modules exist) |
| JSON/YAML code blocks added or modified | L2 (parse + schema) |
| Version references added or changed | L3 (cross-reference) |
| Behavioral guidance added (decision trees, strategies) | L3 (contracts) |
| Forbidden behavior patterns specified | L3 (anti-pattern detection) |
| Simple section reordering or prose editing | L1 if no tests exist, skip otherwise |

#### Common Fixtures

These fixtures appear across all three exemplar test classes:

```python
@pytest.fixture
def skill_path(self) -> Path:
    """Resolve path to the skill file under test."""
    depth = 3  # Adjust based on test file location relative to plugin root
    return Path(__file__).parents[depth] / "skills" / "skill-name" / "SKILL.md"

@pytest.fixture
def skill_content(self, skill_path: Path) -> str:
    """Read the full skill content for assertion."""
    return skill_path.read_text()

@pytest.fixture
def module_path(self) -> Path:
    """Resolve path to a specific module file."""
    depth = 3  # Adjust based on test file location relative to plugin root
    return Path(__file__).parents[depth] / "skills" / "skill-name" / "modules" / "module.md"
```

Adjust `parents[N]` based on your test file's depth relative
to the plugin root.
