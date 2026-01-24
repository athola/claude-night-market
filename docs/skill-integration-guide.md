# Skill Integration Guide

Skills coordinate to solve complex problems by passing data between specialized tools. This guide covers common integration patterns and implementation details.

## Workflow Integration

Workflow skills execute in sequence. For example, an API development pipeline moves from `skill-authoring` to generate the structure, `api-design` to define endpoints, and `testing-patterns` for coverage. It concludes with `doc-updates` and `commit-messages` to finalize the work.

A security review follows a similar chain: `security-scanning` identifies vulnerabilities, `bug-review` and `architecture-review` analyze the findings, and `test-review` verifies coverage before `pr-prep` packages the fixes.

## Knowledge Management

Knowledge skills capture and organize information. In a learning workflow, `memory-palace-architect` designs a spatial structure while `knowledge-intake` processes materials. These concepts are then stored via `digital-garden-cultivator` and practiced through `session-palace-builder`.

Research projects use `knowledge-locator` to find sources, `evidence-logging` for citations, and `structured-output` to format the data, finishing with `imbue-review` to synthesize the report.

## Performance Optimization

Optimizing large systems requires filtering and concurrency. `context-optimization` selects relevant files to fit the context window, while `subagent-dispatching` assigns modules to parallel workers. `systematic-debugging` then isolates root causes before `verification-before-completion` runs regression tests.

For Python applications, `python-async` handles blocking I/O, `python-performance` profiles hotspots, and `condition-based-waiting` replaces sleeps with event triggers.

## Implementation Examples

### API Development Pipeline

Building a user management microservice involves several coordinated steps:

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

Generating tests and documentation directly from the design avoids drift. This pipeline ensures that endpoints, validation, and documentation remain synchronized throughout the development cycle.

### Security Review Automation

A full security audit uses `security-scanning` to find vulnerabilities across SAST and DAST. `bug-review` then analyzes these findings for exploitability, while `architecture-review` validates the system design against threats like injection or CSRF. Finally, `test-review` identifies coverage gaps, and `pr-prep` assembles the remediation plan. This workflow produces an auditable trail, packaging fixes and tests into a single unit for review.

### Learning Acceleration

To master a new framework or language, `memory-palace-architect` creates a scaffold for core concepts (e.g., Rust ownership and lifetimes). `knowledge-intake` filters official documentation and examples into a progressive learning path, which `digital-garden-cultivator` then stores for long-term reference. `session-palace-builder` builds temporary recall exercises for immediate application.

## Integration Patterns

Skills can be combined using sequential chaining, parallel execution, or conditional routing. Sequential chaining passes output from one skill as input to the next, while parallel execution uses `asyncio.gather` for independent tasks. Conditional routing selects a skill based on input characteristics, providing a default if no rules match.

Composite skills wrap multiple specialized tools into a single workflow. This allows for complex coordination while keeping the individual skills focused on single tasks.

## Integration Standards

Effective integration requires standardized interfaces and consistent error handling to prevent chain failures. Load skills dynamically to conserve tokens, and cache results for expensive steps in frequently used workflows. Configuration should be passed at runtime to support different environments, and logging both inputs and outputs simplifies debugging when a link fails.

Common use cases include full software development lifecycles (requirements through maintenance), security operations (detection through prevention), and research pipelines (hypothesis through publication).

## Testing and Validation

Verify integrations by testing complete skill chains and checking interface compatibility. Error propagation tests ensure the system handles failures gracefully across skill boundaries. Before finalizing a workflow, confirm that data flows correctly between steps and that performance remains within acceptable limits. Documentation should reflect the final integrated state, and tests must cover typical use cases to prevent regression.

---

## See Also

- [Superpowers Integration](./superpowers-integration.md) - Superpowers skill integration
- [Plugin Development Guide](./plugin-development-guide.md) - Creating plugins
