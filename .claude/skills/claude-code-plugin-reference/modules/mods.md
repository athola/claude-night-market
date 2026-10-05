# Mods: TypeScript function hooks (2.1.287)

A mod is an ordinary plugin whose `hooks/hooks.json` names one module:
`{"hooks": {...}, "modules": ["./band.tsx"]}`. The module exports
`register(on, options)` and adds hooks shaped `($, e, next)` on events
such as `tool.call`, `prompt.submit`, `prompt.compose`, `session.append`,
`turn.step`, `ui.render` and `command.run`. `$` reaches the engine: UI
(panes, a band above the prompt, status line, toasts), `$.state` and
`$.store`, `$.tool.register`, `$.agent.register`, `$.model.complete`,
timers, files and processes. The module runs in its own environment with
no Node and no DOM, as an ES module that may not use `import()`.

Authoritative sources, in order: the types the engine writes
(`claude-code.d.ts`, beside the bundled `plugin-authoring` skill or in a
loaded mod's `.claude-plugin/types/`), code.claude.com/docs/en/plugins/
mods/, then `Skill(plugin-authoring)`. The API is early access and moves
between releases.

What binds this repo:

- Command hooks keep running alongside mods and are not deprecated.
  Python guards stay in Python.
- A mod that answers `tool.call` itself, without `next`, keeps every
  plugin PreToolUse hook from running. Mods here observe and draw only:
  never answer `tool.call` with a result, hook `tool.check`, or rewrite
  tool input.
- Mods are unsandboxed, can be switched off remotely, and are blocked for
  marketplace plugins where an organization sets `allowManagedModsOnly`.
  Nothing may depend on a mod being loaded.
- An installed plugin runs from its versioned cache, so a mod change
  reaches users only with a version bump.
- `claude plugin validate <dir>` checks the module; `claude plugin test
  <dir>` runs its `*.test.ts` files against the engine. `make test-mods`
  runs both for every plugin that ships a module.

Two ship here. conserve's `hooks/context-band.tsx` draws context fill and
prompt-cache reuse above the prompt beside `context_warning.py`, which
stays the part Claude reads. egregore's `hooks/loop-band.tsx` draws the
active work item and answers `/egregore-loop` without a model turn. Their
kit tests live in each plugin's `mod-tests/`, out of pytest's reach, and
`tests/test_make_test_mods.py` fails if a module ever hooks `tool.call` or
`tool.check`.
