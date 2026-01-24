---
name: validate-plugin-structure
description: detailed checklist and reference guide for manually validating Claude Code plugin structure step-by-step. Use when you need the detailed validation checklist with implementation code samples, want to understand plugin.json schema requirements, or are building validation tooling. For quick automated validation, use /validate-plugin command instead.
triggers:
  - plugin validation checklist
  - plugin.json schema reference
  - plugin structure requirements
  - manual plugin audit
  - build validation tooling
---

# Plugin Structure Validation

This skill validates a Claude Code plugin's directory structure and metadata against required schemas and project conventions.

## Usage

Use this skill when creating new plugins, preparing for distribution, or debugging loading issues. For automated validation, use the `/validate-plugin` command.

## Validation Checklist

### 1. Required Structure

- **plugin.json**: Verify that `.claude-plugin/plugin.json` exists at the plugin root.
- **Metadata**: Confirm the `name` field exists and uses kebab-case (lowercase, hyphens only).
- **Component Isolation**: Component directories (skills, commands, agents, hooks) must be located at the plugin root, not nested within `.claude-plugin/`.

### 2. Directory Structure

If referenced in `plugin.json`, the corresponding directories must exist at the root: `skills/`, `commands/`, `agents/`, and `hooks/`.

### 3. Metadata Schema

- **Required**: `name` (kebab-case).
- **Recommended**: `version` (semver), `description`, `author`, and `license` (e.g., MIT).
- **Optional**: `main` entry point, `provides` capabilities list, `dependencies` with version constraints, and `repository` or `homepage` URLs.

### 4. Component Validation

- **Skills**: Each referenced skill must exist as a `.md` file or within a named directory containing a `SKILL.md`. Files must include YAML frontmatter with `name` and `description` fields and use progressive disclosure for technical details.
- **Commands**: Files must be in Markdown format with YAML frontmatter metadata. All command paths in `plugin.json` must use the `./` prefix.
- **Agents**: Agent definitions must be valid Markdown and use relative paths.

### 5. Path Resolution and Dependencies

All paths in `plugin.json` must be relative (starting with `./`). Use `${CLAUDE_PLUGIN_ROOT}` for dynamic environment references. Dependencies must specify semantic versions (e.g., `">=2.0.0"`) and must not form circular references.

## Implementation Steps

### Step 1: Directory Verification

Confirm the plugin path and change to that directory. If no path is provided, the script should report usage details and exit.

### Step 2: Critical File Check

Verify the existence of `.claude-plugin/plugin.json`. If missing, halt execution and report a critical failure.

### Step 3: Content and Schema Validation

Use a Python script to parse `plugin.json`. Validate that the `name` matches the kebab-case regex. Check for recommended fields and verify that all referenced component paths resolve to existing files. For dependencies, confirm that the format is an object with semantic version strings rather than a flat array.

### Step 4: Directory Mapping

Iterate through the `standard_dirs` list (`skills`, `commands`, `agents`, `hooks`). If `plugin.json` references a component type but the corresponding directory is missing from the root, report a warning.

## Common Issues

- **Incorrect Pathing**: Move `plugin.json` from the root to `.claude-plugin/`.
- **Naming Violations**: Update the `name` field to use only lowercase letters and hyphens.
- **Absolute Paths**: Convert all path references in `plugin.json` to start with `./`.
- **Missing Directories**: Create the standard component directories if they are missing but referenced.

## Technical Standards

Integrate structure validation into CI/CD pipelines to catch issues before distribution. Use semantic versioning for all releases and specify version requirements for dependencies. Maintain standard directory structures to minimize custom path configuration. Document each skill using progressive disclosure to manage context window efficiency.

## Conclusion

Regular validation confirms that a plugin loads correctly across different environments, adheres to project conventions, and maintains interoperability within the ecosystem.
