---
name: Initiative Task
description: Template for tasks related to medium-term initiatives
title: "[INITIATIVE] "
labels: []
assignees: []
body:
  - type: dropdown
    id: initiative
    attributes:
      label: Initiative
      description: Which initiative does this task relate to?
      options:
        - Architecture Review
        - Test Infrastructure Modernization
        - Documentation Drive
        - Cross-Initiative
    validations:
      required: true

  - type: dropdown
    id: phase
    attributes:
      label: Phase
      description: Which phase is this task part of?
      options:
        - Phase 1 (Weeks 1-2)
        - Phase 2 (Weeks 3-6)
        - Phase 3 (Weeks 7-8)
        - Planning/Ongoing
    validations:
      required: true

  - type: dropdown
    id: priority
    attributes:
      label: Priority
      description: What is the priority of this task?
      options:
        - High
        - Medium
        - Low
    validations:
      required: true

  - type: textarea
    id: description
    attributes:
      label: Task Description
      description: Clear description of what needs to be done
      placeholder: Provide a detailed description of the task...
    validations:
      required: true

  - type: textarea
    id: acceptance-criteria
    attributes:
      label: Acceptance Criteria
      description: What are the specific criteria for this task to be considered complete?
      placeholder:
        - [ ] Criteria 1
        - [ ] Criteria 2
        - [ ] Criteria 3
    validations:
      required: true

  - type: textarea
    id: dependencies
    attributes:
      label: Dependencies
      description: Are there any dependencies or blockers?
      placeholder: List any tasks, resources, or external dependencies...

  - type: dropdown
    id: estimated-effort
    attributes:
      label: Estimated Effort
      description: How long do you estimate this task will take?
      options:
        - < 1 day
        - 1-2 days
        - 3-5 days
        - 1 week
        - > 1 week
    validations:
      required: true

  - type: textarea
    id: notes
    attributes:
      label: Additional Notes
      description: Any additional context, questions, or concerns

  - type: checkboxes
    id: checklist
    attributes:
      label: Pre-Implementation Checklist
      description: Ensure these items are addressed before starting implementation
      options:
        - label: Task requirements are clear and understood
          required: false
        - label: Dependencies have been identified and addressed
          required: false
        - label: Acceptance criteria are measurable
          required: false
        - label: Testing approach has been considered
          required: false
