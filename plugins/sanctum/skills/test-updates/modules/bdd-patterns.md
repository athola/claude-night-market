# BDD Patterns Module

## Overview

Provides multiple Behavior-Driven Development styles and patterns for creating expressive, behavior-focused tests.

## Available Styles

| Style | Best For |
|-------|----------|
| Gherkin | Complex workflows, acceptance criteria, cross-team |
| BDD-pytest | Unit/API tests, developer focus |
| Docstring BDD | Simple tests, quick docs |

## Choosing the Right Style

### Decision Guide

| Style | Best For | Complexity | Collaboration |
|-------|----------|------------|----------------|
| Gherkin | Complex workflows, documentation | High | Excellent |
| BDD-pytest | Unit/API tests, developer focus | Medium | Good |
| Docstring BDD | Simple tests, quick docs | Low | Limited |

### Mixing Styles
- Use Gherkin for critical user journeys
- Use BDD-pytest for unit and API tests
- Use Docstring BDD for simple utilities
- Maintain consistency within modules

## Best Practices

### Naming Conventions
- **Tests**: `test_[behavior]_[when]_[expected]`
- **Given/When/Then**: Clear separation of concerns
- **Scenarios**: Describe business value, not technical details

### Test Organization
Group related BDD scenarios in test classes with clear setup and teardown.

---

### Gherkin Style

Feature files with Given/When/Then scenarios for complex user
workflows and cross-team collaboration.

#### Feature File Structure

```gherkin
Feature: Git Workflow Management
  As a developer
  I want to automate git workflows
  So that I can maintain clean commit history

  Scenario: Commit with staged changes
    Given a git repository with staged changes
    When I run the commit workflow
    Then a commit should be created with proper message
    And all tests should pass

  Scenario Outline: Multiple file types
    Given a git repository with staged <file_type> files
    When I run the commit workflow
    Then the commit should reference <file_type>
    And the commit type should be <commit_type>

    Examples:
      | file_type | commit_type |
      | source    | feat       |
      | test      | test       |
      | docs      | docs       |
```

#### Step Definitions

```python
@given('a git repository with staged changes')
def step_given_git_repo_with_changes(context):
    context.repo = create_test_repo()
    context.repo.stage_changes(['file1.py', 'file2.py'])

@when('I run the commit workflow')
def step_when_run_commit_workflow(context):
    context.result = run_commit_workflow(context.repo)

@then('a commit should be created with proper message')
def step_then_commit_created(context):
    assert context.repo.has_commit()
    assert context.repo.last_commit_message().startswith('feat:')
```

#### When to Use

- Complex user workflows
- Acceptance criteria documentation
- Cross-team collaboration
- Living documentation requirements

---

### Pytest Style

BDD-style pytest tests with descriptive names and docstrings
for unit and API testing.

#### Structure Example

```python
class TestGitWorkflow:
    """BDD-style tests for Git workflow operations."""

    @pytest.mark.bdd
    def test_commit_workflow_with_staged_changes(self):
        """
        GIVEN a Git repository with staged changes
        WHEN the user runs the commit workflow
        THEN it should create a commit with proper message format
        AND all tests should pass
        """
        # Given
        repo = create_git_repo()
        repo.stage_changes(['feature.py'])

        # When
        result = run_commit_workflow(repo)

        # Then
        assert result.success is True
        assert repo.has_commit()
        assert repo.last_commit_message().startswith('feat:')

    @pytest.mark.bdd
    def test_commit_workflow_rejects_empty_changes(self):
        """
        GIVEN a Git repository with no staged changes
        WHEN the user runs the commit workflow
        THEN it should reject with appropriate error message
        """
        # Given
        repo = create_git_repo()  # No changes staged

        # When
        result = run_commit_workflow(repo)

        # Then
        assert result.success is False
        assert "no staged changes" in result.error.lower()
```

#### Best Practices

- **Descriptive names**: Describe behavior, not implementation
- **Clear sections**: Use Given/When/Then in docstrings
- **Single responsibility**: One behavior per test
- **Meaningful assertions**: Test specific outcomes

#### When to Use

- Unit tests with behavior focus
- API testing
- Service layer testing
- Developer-facing documentation

---

### Docstring Style

Simple BDD pattern using docstrings for quick behavior
documentation and simple unit tests.

#### Structure Example

```python
def test_git_status_parsing():
    """Test parsing git status output.

    GIVEN git status output with modified and untracked files
    WHEN parsing the status
    THEN it should return structured file information
    AND correctly identify file states
    """
    status_output = """
    M modified_file.py
    A  added_file.py
    ?? untracked_file.py
    """

    result = parse_git_status(status_output)

    assert 'modified_file.py' in result.modified
    assert 'added_file.py' in result.added
    assert 'untracked_file.py' in result.untracked
```

#### Best Practices

- **Clear docstrings**: Include Given/When/Then
- **Simple structure**: Ideal for utilities and helpers
- **Quick documentation**: Minimal overhead for behavior specs
- **Focused tests**: One clear behavior per test

#### When to Use

- Simple unit tests
- Internal module testing
- Quick behavior documentation
- Utility function testing
