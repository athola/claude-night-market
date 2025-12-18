# Graphviz Conventions for Skill Diagrams

## Overview

Process diagrams help visualize skill workflows, decision trees, and error handling. This module defines standard conventions for creating consistent, readable Graphviz diagrams in skills.

## When to Include Diagrams

 **Use diagrams for:**
- Complex decision trees (3+ decision points)
- Multi-step workflows with branches
- Error handling flows
- State transitions
- Tool orchestration sequences

 **Skip diagrams for:**
- Simple linear workflows (just use numbered lists)
- Single decision points
- Purely conceptual relationships (use tables instead)

## Node Type Conventions

### Diamond: Questions/Decisions

**Shape**: `shape=diamond`

**Purpose**: Binary or multiple-choice decision points

**Naming**: Always end with question mark

```dot
digraph {
    node [shape=diamond]
    decision [label="Tests\nexist?"]
}
```

**Example Labels:**
- "Tests exist?"
- "Security critical?"
- "Production code?"
- "Validation passed?"

### Box: Actions/Processes

**Shape**: `shape=box` (default)

**Purpose**: Actions Claude should take

**Naming**: Start with verb (imperative form)

```dot
digraph {
    node [shape=box]
    action [label="Run tests"]
}
```

**Example Labels:**
- "Run tests"
- "Write validation"
- "Generate report"
- "Update documentation"

### Plaintext: Commands/Code

**Shape**: `shape=plaintext`

**Purpose**: Literal commands or code to execute

**Naming**: Show actual syntax

```dot
digraph {
    node [shape=plaintext, fontname="Courier"]
    cmd [label="pytest tests/"]
}
```

**Example Labels:**
- "pytest tests/"
- "git commit -m '...'"
- "make build"
- "./script.sh"

### Ellipse: States/Results

**Shape**: `shape=ellipse`

**Purpose**: Outcomes, states, or results

**Naming**: Descriptive noun phrases

```dot
digraph {
    node [shape=ellipse]
    state [label="Tests\npassing"]
}
```

**Example Labels:**
- "Tests passing"
- "Deployment ready"
- "Security validated"
- "Error state"

### Octagon: Warnings/Stops

**Shape**: `shape=octagon`

**Purpose**: Critical warnings or stop conditions

**Naming**: Imperative warnings

```dot
digraph {
    node [shape=octagon, style=filled, fillcolor=yellow]
    warning [label="STOP\nSecurity risk"]
}
```

**Example Labels:**
- "STOP: Security risk"
- "WARNING: Untested code"
- "HALT: Missing validation"

### Double Circle: Start/End Points

**Shape**: `shape=doublecircle`

**Purpose**: Entry and exit points

```dot
digraph {
    node [shape=doublecircle]
    start [label="Start"]
    end [label="Complete"]
}
```

## Edge Labeling Conventions

### Binary Decisions

Use "yes"/"no" for diamond nodes:

```dot
digraph {
    node [shape=diamond]
    decision [label="Tests\nexist?"]

    node [shape=box]
    action1 [label="Run tests"]
    action2 [label="Write tests"]

    decision -> action1 [label="yes"]
    decision -> action2 [label="no"]
}
```

### Multiple Choice

Use descriptive labels:

```dot
digraph {
    node [shape=diamond]
    severity [label="Priority\nlevel?"]

    node [shape=box]
    critical [label="Fix immediately"]
    high [label="Fix this sprint"]
    low [label="Backlog"]

    severity -> critical [label="critical"]
    severity -> high [label="high"]
    severity -> low [label="low"]
}
```

### Sequential Flow

Use no labels for obvious sequences:

```dot
digraph {
    rankdir=LR
    node [shape=box]

    A [label="Write test"]
    B [label="Run test"]
    C [label="See failure"]

    A -> B -> C
}
```

### Conditional Edges

Use descriptive conditions:

```dot
digraph {
    node [shape=box]
    check [label="Check coverage"]
    improve [label="Add tests"]
    proceed [label="Continue"]

    check -> improve [label="< 80%"]
    check -> proceed [label="≥ 80%"]
}
```

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

## Layout Best Practices

### Direction

**Top to Bottom** (default): Use for most workflows
```dot
digraph {
    rankdir=TB  // or omit, TB is default
}
```

**Left to Right**: Use for sequential processes
```dot
digraph {
    rankdir=LR
}
```

### Grouping with Subgraphs

Group related nodes:

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

### Alignment

Force nodes onto same rank for parallel processes:

```dot
digraph {
    node [shape=box]

    {rank=same; security_check; validation; rate_limit}

    request -> {security_check validation rate_limit}
    {security_check validation rate_limit} -> process
}
```

## Color Usage

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

### Accessible Colors

Avoid red/green only combinations (colorblind accessible):
- Use shapes + colors
- Add text indicators
- Use patterns when possible

## Font and Styling

### Standard Settings

```dot
digraph {
    // Global settings
    graph [fontname="Arial", fontsize=10]
    node [fontname="Arial", fontsize=10]
    edge [fontname="Arial", fontsize=9]

    // For code/commands
    node [shape=plaintext, fontname="Courier"]
    cmd [label="pytest"]
}
```

### Text Wrapping

Use `\n` for line breaks in labels:

```dot
node [label="This is a long label\nthat spans\nmultiple lines"]
```

Aim for 10-15 characters per line maximum.

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

## Validation Checklist

Before including a diagram in a skill:

- [ ] All decision nodes are diamonds with questions
- [ ] All action nodes are boxes with verbs
- [ ] Binary decisions use "yes"/"no" labels
- [ ] Complex decisions use descriptive labels
- [ ] Commands/code use plaintext shape
- [ ] Colors are semantic and accessible
- [ ] Text wraps at reasonable width
- [ ] Start/end points marked (if applicable)
- [ ] Critical warnings use octagon shape
- [ ] Direction (TB/LR) suits the workflow
- [ ] Font is readable (10-12pt)
- [ ] Diagram adds value (not just decoration)

## Rendering

### In Markdown Skills

Use fenced code blocks:

````markdown
```dot
digraph example {
    start -> process -> end
}
```
````

### Command-Line Rendering

```bash
# Generate PNG
dot -Tpng workflow.dot -o workflow.png

# Generate SVG (recommended for documentation)
dot -Tsvg workflow.dot -o workflow.svg

# Generate PDF
dot -Tpdf workflow.dot -o workflow.pdf
```

## Anti-Patterns

###  Overly Complex Diagrams

**Problem**: Too many nodes, hard to follow

**Solution**: Break into multiple focused diagrams or use hierarchical grouping

###  Missing Labels

**Problem**: Unlabeled edges in complex flows

**Solution**: Always label decision edges, optional for obvious sequences

###  Inconsistent Shapes

**Problem**: Using box for both questions and actions

**Solution**: Follow shape conventions consistently

###  Decoration-Only Diagrams

**Problem**: Diagram doesn't add information beyond text

**Solution**: Only include diagrams that clarify complex flows

###  Unreadable Text

**Problem**: Font too small or labels too long

**Solution**: Use 10-12pt fonts, wrap long labels

## Summary

Standard Graphviz conventions:
- **Diamond**: Questions/decisions
- **Box**: Actions/processes
- **Plaintext**: Commands/code
- **Ellipse**: States/results
- **Octagon**: Warnings/stops
- **Double circle**: Start/end

Label edges clearly, use semantic colors, and only include diagrams that add value beyond text descriptions.
