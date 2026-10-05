# P0: baseline the gate and judge suites

Run every suite from inside its plugin directory. Root pytest sets
`norecursedirs = plugins/*`, so running from the repo root silently
collects nothing (or raises `ImportPathMismatchError`). Every `cd`
in this skill is relative to the repo root: start each command block
from there.

```bash
cd plugins/egregore
uv run pytest tests/ -q
```

Expected (2026-07-02): `477 passed` in about 2 seconds, preceded by a
coverage table.

```bash
cd plugins/egregore
uv run pytest tests/test_config.py tests/test_quality_gate.py -q
```

Expected: `27 passed`. `tests/test_config.py` alone is `13 passed` and
includes the two completion-integrity guards:
`test_completion_integrity_opt_in_roundtrip` and
`test_completion_integrity_loads_from_raw_json` (the real user opt-in
path, added in cd903cbf. It also guards the field against silent
removal, because `_filter_fields` would drop the key).

```bash
cd plugins/herald
uv run pytest tests/ -q
```

Expected: `105 passed` in under 2 seconds. This suite contains
`test_llm_timeout_fits_within_hook_timeout`, which asserts
`LLM_TIMEOUT_SECONDS` (8) is strictly below the Stop-hook timeout
registered in `plugins/herald/hooks/hooks.json` (10).

```bash
cd plugins/imbue
uv run pytest tests/unit/skills/test_proof_of_work.py -q
```

Expected: `17 passed`. Note: imbue's pytest addopts force coverage
artifacts on every run. There is no dedicated test for the
verifier-integrity module itself (verified 2026-07-02 by grepping
`plugins/imbue/tests/` for `verifier-integrity`): the module is prose,
covered only by the skill-structure test above.

Smoke-test the herald judge directly. All three probes below were run
and their outputs captured verbatim on 2026-07-02:

```bash
echo '{"session_id":"probe","transcript_path":"/nonexistent"}' \
  | python3 plugins/herald/hooks/double_shot_latte.py
```

Expected:

```json
{"decision": "approve", "reason": "Double Shot Latte: No transcript available; allowing stop."}
```

```bash
D=$(mktemp -d)
printf '%s\n' '{"type":"assistant","message":{"role":"assistant","content":[{"type":"text","text":"Now let me fix the failing tests."}]}}' \
  > "$D/t.jsonl"
echo "{\"session_id\":\"p1\",\"transcript_path\":\"$D/t.jsonl\"}" \
  | python3 plugins/herald/hooks/double_shot_latte.py
```

Expected:

```json
{"decision": "block", "reason": "Double Shot Latte: Assistant stated explicit intent to keep working."}
```

Gate P0 branches:

- Pass counts lower than stated, or any failure: the repo has drifted
  since 2026-07-02. Stop the campaign. Triage with
  `night-market-debugging-playbook`, then update the counts in this
  skill's Provenance section before proceeding.
- `ImportPathMismatchError` or `no tests ran`: you ran pytest from the
  wrong directory. Re-run from inside the plugin.
- Hook probe emits nothing or a traceback: the hook contract is broken
  (it must always exit 0 and print a decision). That is a P0 incident,
  not a campaign step. File it.
