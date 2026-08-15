# Asset Sweep

Step 3 and step 4. Map the research findings onto asset classes, then
update only the classes a finding implicates.

A blanket rewrite is the failure mode here. This repo holds 24 plugins,
208 plugin skills, 163 commands, 56 agents, 711 hook files, 15 local
skills, and 9 rules. Touching all of them because one model shipped
produces a diff nobody can review and buries the change that mattered.

## Impact table

| Asset class | Location | Owner check |
|-------------|----------|-------------|
| Gate vocabularies | `scripts/check_*.py` | Unit tests |
| Agent frontmatter | `plugins/*/agents/*.md` | `check_agent_model_matrix.py` |
| Plugin skills | `plugins/*/skills/**/SKILL.md` | `check_agent_model_matrix.py` |
| Local skills | `.claude/skills/*/SKILL.md` | `check_upstream_drift.py` |
| Commands | `plugins/*/commands/*.md` | `check_upstream_drift.py` |
| Hooks | `plugins/*/hooks/**` | Plugin test suites |
| Docs of record | `docs/agent-model-matrix.md` | `check_agent_model_matrix.py` |
| Rules | `.claude/rules/*.md` | Review |
| Model routing | `plugins/egregore/skills/summon/modules/model-routing.md` | Review |

## Routing findings to classes

| Finding shape | Classes to touch |
|---------------|------------------|
| A tier shipped | Gate vocabularies, docs of record, model routing |
| An effort level shipped | Gate vocabularies, docs of record |
| A model ID was retired | Dated-ID backlog, docs of record |
| A hook event was added or renamed | Hooks, plugin reference |
| A tool or field changed shape | Commands, skills that call it |
| Context window changed | Docs of record, any skill quoting a limit |

A finding that implicates no class is recorded in the migration report
and closed. That record is what stops the next run researching it
again.

## Order of operations

Vocabularies first, then the assets that depend on them.

1. **Widen gate vocabularies.** A tier cannot be pinned anywhere until
   the gate accepts it. Doing this last means every intermediate commit
   fails the gate.
2. **Update the docs of record.** `docs/agent-model-matrix.md` is
   checked against disk, so it moves with the roster.
3. **Update assets.** Agents, skills, commands, hooks.
4. **Re-run the owner check for each class touched.**

## Rules that do not bend

- **Widen, never narrow.** Removing an accepted value breaks assets
  that currently pass. A retired model ID stays accepted until every
  reference is gone, and only then is it dropped.
- **Tier aliases in agent frontmatter, never dated IDs.**
  `check_agent_model_matrix.py` enforces this and a new model does not
  reverse it. A shipped tier widens the vocabulary. It does not
  reintroduce dated pins.
- **A new tier needs a placement rule.** Adding a row to the matrix
  table without saying which task shapes belong in it leaves the next
  reader guessing, and guesses become misrouted agents.
- **External captures are read-only.** Files under `data/staging/` are
  other people's text. The detector skips them and so does the sweep.
- **Reassigning an agent's tier is a separate change.** A sweep makes a
  new tier available. Deciding that a given agent should move into it
  is a judgment call with its own rationale and its own review.

## Finding the surface

```bash
# Every file mentioning a model, by asset class
rg -l 'claude-(opus|sonnet|haiku|fable)-[0-9]' plugins .claude docs

# Frontmatter tier pins only
rg -n '^model:' plugins/*/agents/*.md

# What the detector currently counts against the ratchet
python3 scripts/check_upstream_drift.py --json \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["dated_ids_found"], "found,", d["dated_ids_backlog"], "allowed")'
```

## Lowering the ratchet

When a sweep removes dated IDs, lower `ratchets.dated_ids_backlog` to
the new count in the same change. A backlog left above the real count
is slack that silently absorbs the next regression.

The detector prints the available slack whenever the count has fallen,
so this is a prompt rather than something to remember.
