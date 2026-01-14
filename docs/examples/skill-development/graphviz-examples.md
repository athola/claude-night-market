# Graphviz Examples for Skill Diagrams

Comprehensive examples for creating process diagrams in skills. For conventions and quick reference, see the [graphviz-conventions module](../../../plugins/abstract/skills/skill-authoring/modules/graphviz-conventions.md).

## Complete Example: TDD Workflow

```dot
digraph TDD {
    // Graph settings
    rankdir=TB
    node [style=filled, fillcolor=lightblue]

    // Start
    node [shape=doublecircle, fillcolor=lightgreen]
    start [label="Start"]

    // Red phase
    node [shape=box, fillcolor=lightcoral]
    write_test [label="Write\nfailing test"]
    run_test [label="Run test"]

    node [shape=diamond, fillcolor=lightyellow]
    test_fails [label="Test\nfails?"]

    node [shape=octagon, fillcolor=yellow]
    warning [label="STOP\nTest must fail\nfirst"]

    // Green phase
    node [shape=box, fillcolor=lightgreen]
    write_code [label="Write minimal\nimplementation"]
    run_again [label="Run test\nagain"]

    node [shape=diamond, fillcolor=lightyellow]
    test_passes [label="Test\npasses?"]

    // Refactor phase
    node [shape=box, fillcolor=lightblue]
    refactor [label="Refactor\ncode"]
    run_all [label="Run all\ntests"]

    node [shape=diamond, fillcolor=lightyellow]
    all_pass [label="All tests\npass?"]

    node [shape=diamond, fillcolor=lightyellow]
    more_features [label="More\nfeatures?"]

    // End
    node [shape=doublecircle, fillcolor=lightgreen]
    end [label="Complete"]

    // Flow
    start -> write_test
    write_test -> run_test
    run_test -> test_fails

    test_fails -> warning [label="no"]
    warning -> write_test [label="fix test"]
    test_fails -> write_code [label="yes"]

    write_code -> run_again
    run_again -> test_passes

    test_passes -> write_code [label="no"]
    test_passes -> refactor [label="yes"]

    refactor -> run_all
    run_all -> all_pass

    all_pass -> refactor [label="no"]
    all_pass -> more_features [label="yes"]

    more_features -> write_test [label="yes"]
    more_features -> end [label="no"]
}
```

## Layout Examples

### Grouping with Subgraphs

```dot
digraph {
    subgraph cluster_validation {
        label="Validation Phase"
        style=filled
        fillcolor=lightgray

        node [fillcolor=white]
        check_input [label="Check input"]
        validate_format [label="Validate format"]
        sanitize [label="Sanitize"]
    }

    subgraph cluster_processing {
        label="Processing Phase"
        style=filled
        fillcolor=lightblue

        node [fillcolor=white]
        process [label="Process data"]
        transform [label="Transform"]
    }

    check_input -> validate_format -> sanitize
    sanitize -> process -> transform
}
```

### Rank Alignment for Parallel Processes

```dot
digraph {
    node [shape=box]

    {rank=same; security_check; validation; rate_limit}

    request -> {security_check validation rate_limit}
    {security_check validation rate_limit} -> process
}
```

## Common Patterns

### Binary Decision Tree

```dot
digraph {
    node [shape=diamond]
    q1 [label="Q1?"]
    q2 [label="Q2?"]

    node [shape=box]
    a [label="Action A"]
    b [label="Action B"]
    c [label="Action C"]

    q1 -> a [label="yes"]
    q1 -> q2 [label="no"]
    q2 -> b [label="yes"]
    q2 -> c [label="no"]
}
```

### Error Handling Flow

```dot
digraph {
    node [shape=box]
    operation [label="Execute\noperation"]

    node [shape=diamond]
    success [label="Success?"]

    node [shape=box]
    handle_error [label="Handle\nerror"]
    log [label="Log error"]
    retry [label="Retry"]

    node [shape=ellipse]
    complete [label="Complete"]

    operation -> success
    success -> complete [label="yes"]
    success -> handle_error [label="no"]
    handle_error -> log
    log -> retry
    retry -> operation
}
```

### State Machine

```dot
digraph {
    node [shape=ellipse]
    idle [label="Idle"]
    running [label="Running"]
    paused [label="Paused"]
    error [label="Error"]

    node [shape=doublecircle]
    complete [label="Complete"]

    idle -> running [label="start"]
    running -> paused [label="pause"]
    paused -> running [label="resume"]
    running -> error [label="fail"]
    error -> running [label="retry"]
    running -> complete [label="finish"]
}
```

## Color Reference

### Semantic Colors

```dot
digraph {
    // Success/Green phase
    node [fillcolor=lightgreen]
    success [label="Tests pass"]

    // Warning/Caution
    node [fillcolor=yellow]
    caution [label="Review needed"]

    // Error/Red phase
    node [fillcolor=lightcoral]
    failure [label="Test fails"]

    // Process/Neutral
    node [fillcolor=lightblue]
    process [label="Execute"]

    // Info/Note
    node [fillcolor=lightyellow]
    info [label="Check status"]
}
```

## Rendering Commands

```bash
# Generate PNG
dot -Tpng workflow.dot -o workflow.png

# Generate SVG (recommended for documentation)
dot -Tsvg workflow.dot -o workflow.svg

# Generate PDF
dot -Tpdf workflow.dot -o workflow.pdf
```

## Anti-Patterns

### Overly Complex Diagrams

**Problem**: Too many nodes, hard to follow

**Solution**: Break into multiple focused diagrams or use hierarchical grouping

### Missing Labels

**Problem**: Unlabeled edges in complex flows

**Solution**: Always label decision edges, optional for obvious sequences

### Inconsistent Shapes

**Problem**: Using box for both questions and actions

**Solution**: Follow shape conventions consistently

### Decoration-Only Diagrams

**Problem**: Diagram doesn't add information beyond text

**Solution**: Only include diagrams that clarify complex flows

### Unreadable Text

**Problem**: Font too small or labels too long

**Solution**: Use 10-12pt fonts, wrap long labels
