# Cartograph Plugin - Project Brief

**Date**: 2026-04-03
**Status**: Draft

## Problem Statement

**Who**: Developers using Claude Code with night-market plugins
**What**: Claude analyzes and describes architecture, workflows,
and data flows in text but cannot produce visual diagrams.
**Where**: Code review, onboarding, planning, documentation.
**Why**: Visual diagrams communicate structure faster than text.
A single architecture diagram replaces paragraphs of description.
**Current State**: Snip (reference) solves this with Electron +
Mermaid but requires a desktop app. We have Mermaid Chart MCP
available but no skill to generate diagram content from code.

## Goals

1. Analyze codebases and produce structural models
   (imports, call graphs, data flows, plugin relationships)
2. Generate Mermaid syntax from those models
3. Render diagrams via Mermaid Chart MCP server
4. Support multiple diagram types: architecture, data flow,
   workflow, class/module, and dependency graphs
5. Use claude-night-market itself as the exemplar codebase

## Constraints

### Technical

- Must work within Claude Code plugin/skill system
- Rendering via existing Mermaid Chart MCP (no new engine)
- Terminal-first (no desktop app dependency)
- Python for analyzers (ecosystem standard)

### Integration

- Mermaid Chart MCP for rendering
- Scry plugin for optional GIF/media post-processing
- Existing analysis patterns from feature-dev, gauntlet

### Won't Have (v1)

- No desktop app or Electron shell
- No screenshot annotation (snip's territory)
- No interactive diagram editing
- No custom rendering engine

## Selected Approach

**Cartograph plugin with hybrid agent architecture**
(Approaches 2+4 from brainstorm).

A dedicated plugin containing:

- **cartograph:explorer agent** - explores codebases, builds
  structural models (JSON) of imports, call graphs, data flows
- **cartograph:diagram skill** - converts structural models to
  Mermaid syntax and renders via MCP
- **cartograph:visualize command** - user-facing entry point
  (e.g., `/visualize architecture`, `/visualize data-flow`)

### Rationale

- Clean separation from existing plugins (scry = recordings,
  cartograph = diagrams)
- Agent provides systematic, repeatable code analysis
- Skill handles the Mermaid generation with templates per
  diagram type
- Mermaid MCP handles rendering (no new infrastructure)

### Trade-offs Accepted

- **New plugin overhead**: More files to maintain, but clean
  ownership boundaries justify it.
- **Agent dispatch cost**: Explorer agent uses tokens, but
  produces a reusable structural model that multiple diagram
  types can consume.

### Rejected Approaches

- **Scry extension**: Diagrams are a different concern from
  recordings. Would blur scry's focus.
- **Skill-only**: No programmatic analysis means inconsistent
  quality. Claude's native analysis is good but not repeatable.

## Next Steps

1. Specification: define diagram types, model schema, skill
   interfaces
2. Planning: implementation tasks with dependency ordering
3. Execution: build plugin with TDD
