---
description: Bootstrap speckit workflow at the start of a Claude session
---

Initialize the Spec Driven Development workflow for this session:

1. **Verify Repository Context**
   - Confirm `.specify/` directory exists in the project root
   - Check for required scripts in `.specify/scripts/bash/`
   - Validate templates are available

2. **Load Orchestrator Skill**
   - Load `speckit-orchestrator` for workflow coordination
   - This skill maps commands to complementary superpowers skills

3. **Load Persistent State ("presence")**
   - Read `.specify/memory/constitution.md` (constraints and principles)
   - Detect the latest `spec.md` / `plan.md` / `tasks.md` and current workflow status
   - Capture a quick agent-state snapshot for the session (available skills/plugins, intended command, constraints)

4. **Initialize Progress Tracking**
   - Create TodoWrite items for workflow phases:
     - [ ] Repository context verified
     - [ ] Prerequisites validated
     - [ ] Command-specific skills loaded
   - Mark items complete as verified

5. **Proceed with Speckit Workflow**
   - Run your intended `/speckit-*` command:
     - `/speckit-specify` - Create feature specifications
     - `/speckit-clarify` - Refine specifications with targeted questions
     - `/speckit-plan` - Generate implementation plans
     - `/speckit-tasks` - Create dependency-ordered tasks
     - `/speckit-implement` - Execute implementation tasks
     - `/speckit-analyze` - Cross-artifact consistency analysis
     - `/speckit-checklist` - Generate requirement quality checklists
     - `/speckit-constitution` - Manage project principles

6. **Session Persistence**
   - Re-run `/speckit-startup` at the beginning of each new Claude session
   - The orchestrator maintains context across speckit commands
