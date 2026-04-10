# Test Enhancement Module

## Overview

Improves existing tests by applying BDD patterns, adding edge cases, and increasing test quality. Transforms basic tests into detailed behavior specifications.

## Enhancement Strategies

### 1. BDD Pattern Application
Transforms traditional tests into BDD-style tests (details below).

### 2. Edge Case Expansion
Adds detailed edge case testing (details below).

### 3. Test Organization
Improves test structure and maintainability (details below).

## Quality Enhancement Rules

### The Rule of Three
For every assertion, add:
1. **Positive case**: Expected behavior
2. **Negative case**: Error handling
3. **Edge case**: Boundary condition

### AAA Pattern (Arrange-Act-Assert)
```python
def test_workflow():
    # Arrange - Setup everything needed
    context = create_test_context()
    expected = prepare_expected_result()

    # Act - Perform the action
    result = perform_action(context)

    # Assert - Verify outcomes
    assert result == expected
```

### Test Data Factory Pattern
Create reusable test data factories for consistent test setup.

## Enhancement Checklist

For each existing test:
- [ ] Add BDD-style docstring with Given/When/Then
- [ ] Include edge cases and error scenarios
- [ ] Use descriptive test names
- [ ] Add appropriate fixtures
- [ ] Verify test independence
- [ ] Add performance assertions if relevant
- [ ] Include behavior documentation
- [ ] Mock external dependencies appropriately

---

### BDD Transformation

Transforms traditional tests into BDD-style tests with clear
behavior specifications.

#### Before: Traditional Test

```python
def test_commit():
    repo = GitRepo()
    repo.add('file.txt')
    result = repo.commit('message')
    assert result is True
```

#### After: BDD-Style Test

```python
@pytest.mark.bdd
def test_commit_workflow_with_staged_file():
    """
    GIVEN a Git repository with a staged file
    WHEN the user commits with a message
    THEN the commit should be created successfully
    AND the commit message should match
    """
    # Given
    repo = GitRepo()
    repo.add('file.txt')

    # When
    result = repo.commit('Add new feature')

    # Then
    assert result is True
    assert repo.get_last_commit_message() == 'Add new feature'
```

#### Transformation Steps

1. **Add descriptive test name**: Describe behavior, not implementation
2. **Add BDD docstring**: Include Given/When/Then clauses
3. **Structure test with AAA**: Arrange-Act-Assert
4. **Add specific assertions**: Test behavior, not just truthiness

---

### Edge Cases

Systematically adds detailed edge case testing to existing tests.

#### The Rule of Three

For every assertion, add:
1. **Positive case**: Expected behavior
2. **Negative case**: Error handling
3. **Edge case**: Boundary condition

#### Example Expansion

**Original:**
```python
def test_parse_number():
    assert parse_number("123") == 123
```

**Enhanced:**
```python
@pytest.mark.parametrize("input_str,expected,description", [
    ("123", 123, "valid positive integer"),
    ("-456", -456, "valid negative integer"),
    ("0", 0, "zero value"),
    ("3.14", 3.14, "valid float"),
    ("1e5", 100000, "scientific notation"),
])
def test_parse_number_valid_inputs(input_str, expected, description):
    """
    GIVEN various valid number strings
    WHEN parsing the string
    THEN it should return the correct number
    """
    assert parse_number(input_str) == expected

@pytest.mark.parametrize("invalid_input", [
    "abc",
    "",
    "12.34.56",
    "1,234",
    None,
])
def test_parse_number_invalid_inputs(invalid_input):
    """
    GIVEN invalid number inputs
    WHEN parsing the string
    THEN it should raise a ValueError
    """
    with pytest.raises(ValueError):
        parse_number(invalid_input)
```

#### Common Edge Cases

- **Strings**: Empty, whitespace, special characters, unicode
- **Numbers**: Zero, negative, maximum/minimum values, infinity
- **Collections**: Empty, single item, maximum capacity
- **Dates**: Leap years, timezone changes, daylight saving
- **Files**: Missing, permissions, full disk, network errors

---

### Organization Patterns

Restructures tests for better maintainability and clarity.

#### Test Organization Example

```python
class TestGitRepository:
    """BDD-style test suite for GitRepository operations."""

    @pytest.fixture(autouse=True)
    def setup_repo(self, tmp_path):
        """Setup a test repository for each test."""
        self.repo_path = tmp_path / "test_repo"
        self.repo = GitRepository(self.repo_path)
        self.repo.init()

    @pytest.mark.bdd
    def test_init_creates_git_directory(self):
        """
        GIVEN a directory path
        WHEN initializing a git repository
        THEN it should create a .git directory
        """
        assert (self.repo_path / ".git").exists()

    @pytest.mark.bdd
    def test_init_with_existing_repo_raises_error(self):
        """
        GIVEN an existing git repository
        WHEN initializing again
        THEN it should raise RepositoryError
        """
        with pytest.raises(RepositoryError):
            GitRepository(self.repo_path).init()
```

#### AAA Pattern (Arrange-Act-Assert)

```python
def test_workflow():
    # Arrange - Setup everything needed
    context = create_test_context()
    expected = prepare_expected_result()

    # Act - Perform the action
    result = perform_action(context)

    # Assert - Verify outcomes
    assert result == expected
```

#### Test Data Factory Pattern

```python
class TestDataFactory:
    """Factory for creating test data."""

    @staticmethod
    def create_git_repo(branch="main", with_commits=False):
        repo = GitRepository()
        repo.init(branch)

        if with_commits:
            repo.add("README.md")
            repo.commit("Initial commit")

        return repo

    @staticmethod
    def create_user(role="user", **overrides):
        default_user = {
            "name": "Test User",
            "email": "test@example.com",
            "role": role,
        }
        default_user.update(overrides)
        return User(**default_user)
```
