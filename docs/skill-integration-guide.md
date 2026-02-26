# Skill Integration Guide

Integrating skills allows specialized tools to pass data and state between one another. This guide details patterns for chaining skills into functional workflows.

## Workflow Chaining

Chaining skills in sequence creates a pipeline where the output of one stage feeds the next. For example, an API development workflow typically moves from `skill-authoring` to scaffold the project structure, to `api-design` for endpoint definition, and finally to `testing-patterns` for coverage analysis. The process finishes with `doc-updates` and `commit-messages`.

Security reviews follow a similar sequence: `security-scanning` identifies potential vulnerabilities, `bug-review` and `architecture-review` analyze those findings for exploitability, and `test-review` verifies remediation before `pr-prep` stages the fixes.

## State and Knowledge Management

Knowledge-focused skills capture and structure project information. In a learning or onboarding workflow, `memory-palace-architect` defines a spatial structure for core concepts, while `knowledge-intake` processes raw materials. `digital-garden-cultivator` then stores these concepts for long-term reference, and `session-palace-builder` generates recall exercises.

Research workflows use `knowledge-locator` to identify sources, `evidence-logging` for maintaining citations, and `structured-output` to format data. The `imbue-review` skill then synthesizes these components into a report.

## Performance and Resource Optimization

Large-scale operations require active context management and concurrency. `context-optimization` filters files to keep the working set within the context window, while `subagent-dispatching` delegates modules to parallel workers. `systematic-debugging` then isolates root causes before `verification-before-completion` executes regression tests.

For Python-specific performance, `python-async` manages blocking I/O, `python-performance` identifies hotspots, and `condition-based-waiting` uses event triggers instead of static sleeps to reduce idle time.

## Implementation Examples

### API Development Pipeline

The following example shows how to coordinate a user management microservice setup using skill calls:

```python
# Design API and data models
api_design_skill = load_skill('api-design')
endpoint_design = api_design_skill.design_rest_api(
    resource='users',
    operations=['create', 'read', 'update', 'delete', 'list']
)

# Add unit and integration tests
testing_skill = load_skill('testing-patterns')
test_suite = testing_skill.generate_api_tests(endpoints=endpoint_design)

# Generate OpenAPI documentation
doc_skill = load_skill('doc-updates')
api_docs = doc_skill.generate_api_documentation(endpoints=endpoint_design)
```

Generating tests and documentation directly from the design output prevents drift. This pipeline ensures that endpoints, validation logic, and documentation remain synchronized throughout the cycle.

### Security Review Automation

Security audits use `security-scanning` for SAST and DAST analysis. `bug-review` evaluates findings for exploitability, and `architecture-review` validates the design against threats like injection. `test-review` then identifies coverage gaps, while `pr-prep` assembles the remediation plan. This produces an auditable trail, packaging fixes and tests into a single unit for review.

### Learning Acceleration

To learn a new framework, `memory-palace-architect` scaffolds core concepts, such as Rust's ownership model. `knowledge-intake` filters documentation and examples into a progressive path, which `digital-garden-cultivator` stores. `session-palace-builder` builds temporary recall exercises for immediate application.

## Integration Patterns

Skills combine through sequential chaining, parallel execution, or conditional routing. Sequential chaining passes output from one skill as input to the next. Parallel execution uses `asyncio.gather` for independent tasks. Conditional routing selects a skill based on input characteristics and uses a default if no specific rules match.

Composite skills wrap specialized tools into a single workflow. This allows for complex coordination while keeping individual skills focused on single tasks.

## Technical Standards

Integration relies on standardized interfaces and error handling to prevent chain failures. Loading skills dynamically helps conserve tokens, and caching results for expensive steps improves performance in frequently used workflows. Configuration should be passed at runtime to support different environments. Logging both inputs and outputs simplifies debugging when a link in the chain fails.

## Verification

Testing complete skill chains verifies that data flows correctly between steps and that performance remains within limits. propagation tests confirm the system handles failures across skill boundaries. Documentation should reflect the final integrated state, and tests must cover typical use cases to prevent regression.

---

## See Also

- [Superpowers Integration](../book/src/reference/superpowers-integration.md)
- [Plugin Development Guide](./plugin-development-guide.md)
