# Workflows: one per plugin, discovered by convention

A plugin can ship dynamic-workflow scripts alongside its skills,
commands, agents and hooks. Verified on disk 2026-08-23 against the
installed official marketplace, not from documentation alone.

- **Location**: `workflows/` at the plugin root. Two official plugins
  use it today (`claude-security/workflows/scan.js`,
  `code-modernization/workflows/*.js`), and neither declares a
  `workflows` key in `plugin.json`, so discovery is by convention. The
  manifest field exists only to point somewhere else.
- **Invocation**: namespaced, `/plugin-name:workflow-name`, where the
  name comes from the script's `meta.name`.
- **Format**: JavaScript opening with a literal
  `export const meta = { name, description, whenToUse?, phases? }`.
  The body uses `agent()`, `pipeline()`, `parallel()`, `phase()` and
  `log()`, and may `await` and `return` at top level.
- **Not an ES module.** The `export` and the top-level `return` cannot
  coexist in real ESM, so `node --check` on a valid script reports
  "Illegal return statement". The runtime extracts `meta` and runs the
  body inside an async function. Any validator must wrap before it
  checks, or check `meta` structurally and leave syntax to the runtime.
- **Permissions**: subagents spawned by a workflow run in `acceptEdits`
  and inherit the tool allowlist, whatever the session's permission
  mode.

Every plugin in `plugins/` ships one. Each encodes the fan-out that
plugin's flagship work already describes: `scribe/doc-sweep.js` runs
its four reviewers over one document, `parseltongue/python-sweep.js`
runs its four specialists over the same Python, `conjure/provider-sweep.js`
asks every provider whether this machine can call it.

Two conventions hold across all of them, both because a violation
fails at dispatch time rather than at author time:

- A script that cannot start returns `{started: false, reason, next}`
  instead of dispatching agents against missing input. `next` names
  the command that produces what was missing.
- No script calls `Date.now()`, `Math.random()`, argless `new Date()`
  or `import()`. The first three throw, because a run has to replay
  identically from its journal on resume; `import()` fails the script
  before the run starts.

`tests/test_shipped_workflows.py` is the gate: it fails when a plugin
ships none, when `meta` is not the first statement, when `meta.name`
disagrees with the filename, or when a forbidden call appears.

The capabilities reference carries a workflow table now, and
`tests/test_shipped_workflows.py` fails if a shipped script has no
row, so the table cannot drift behind the directory.

One gap stays: `validate_plugin.py` iterates skills, commands, agents
and hooks only, so a fifth asset type is invisible to per-plugin
validation. The root gate covers what that would have caught, which
is why this is a gap rather than a defect. Analysis and the proposed
sequence: `reports/dynamic-workflows-integration-2026-08-23.md`
(machine-local).
