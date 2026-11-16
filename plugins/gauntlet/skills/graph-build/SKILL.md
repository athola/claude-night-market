---
name: graph-build
description: Builds or updates the code knowledge graph via tree-sitter AST and SQLite. Use when setting up the graph before search or blast-radius analysis.
---

# Build Code Knowledge Graph

Build or update the `.gauntlet/graph.db` knowledge graph
for the current codebase.

## Steps

1. **Detect target**: Use the current working directory
   or a user-specified path.

2. **Check for existing graph**: If `.gauntlet/graph.db`
   exists, run an incremental update. Otherwise, run a
   full build.

3. **Run the build script**:

   For full build:
   ```bash
   uv run --project ${CLAUDE_PLUGIN_ROOT} python \
     ${CLAUDE_PLUGIN_ROOT}/scripts/graph_build.py <dir>
   ```

   For incremental update:
   ```bash
   uv run --project ${CLAUDE_PLUGIN_ROOT} python \
     ${CLAUDE_PLUGIN_ROOT}/scripts/graph_build.py <dir> --incremental
   ```

   The build runs in the plugin's own environment because
   a system `python3` may lack tree-sitter. Without it a
   build exits 2 with an `error` key rather than reporting
   files it did not parse.

   An incremental update diffs against `--base-ref`, which
   defaults to the commit of the last successful build.
   Commits made since then are re-parsed. A graph built
   before that commit was recorded falls back to `HEAD`,
   which covers uncommitted changes only: run a full build
   once.

4. **Report results**: Show the JSON output including
   files parsed, nodes created, edges created, and
   duration.

5. **Suggest next steps**: Recommend searching the graph
   or running blast radius analysis.

## When To Use

- At the start of a session to build structural awareness
- After significant code changes to update the graph
- Before running blast radius analysis or flow tracing
- When the user asks about codebase structure

## When NOT To Use

- Querying a graph that already exists (use `gauntlet:graph-search`)
- Building the challenge knowledge base (use `gauntlet:extract`)

## What Gets Parsed

The graph extracts nodes (File, Class, Function, Type,
Test) and edges (CALLS, IMPORTS_FROM, INHERITS, CONTAINS,
IMPLEMENTS, TESTED_BY) from 20+ languages including
Python, JavaScript, TypeScript, Go, Rust, Java, C/C++,
Ruby, and PHP.

## Storage

- Database: `.gauntlet/graph.db` (SQLite with WAL mode)
- Auto-creates `.gauntlet/.gitignore` to prevent commits
- Incremental updates use SHA-256 hashing to skip
  unchanged files
- Each `edges` row has a `resolution` column recording how a
  CALLS target was found: `exact` (module qualifier, `self`/`cls`
  scope, or a unique definition), `name_guess` (a method picked by
  bare name on a receiver of unknown type, or a bare call that
  matched several definitions and only one sits in the caller's
  own `plugins/<name>/`, as with vendored copies), or empty (declared
  edge, external call, or a row from a graph built before the
  column existed). Treat `name_guess` edges as unconfirmed: blast
  radius lists them under `name_guess_callers`. A
  database lacking the column gains it when opened.
- Each build records `gauntlet_version` in the `metadata`
  table. At session start, a graph built by an older
  version is rebuilt in the background (log:
  `.gauntlet/rebuild.log`). Opt out with
  `{"rebuild_on_upgrade": false}` in
  `.gauntlet/config.json`.

## Exit Criteria

- [ ] `.gauntlet/graph.db` exists and is a valid SQLite file after
  the skill completes; `.gauntlet/.gitignore` exists to prevent
  the database from being committed
- [ ] Build report JSON includes all four keys: `files_parsed`,
  `nodes_created`, `edges_created`, `duration`; values are
  non-zero for non-empty codebases
- [ ] Incremental update path used when `.gauntlet/graph.db` already
  exists (script invoked with `--incremental`); full build only
  on first run
- [ ] Next-step suggestions presented to the user: search the graph
  or run blast-radius analysis
