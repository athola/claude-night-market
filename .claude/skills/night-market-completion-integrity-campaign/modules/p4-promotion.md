# P4: promotion through change control

Flipping `completion_integrity` to default-on changes the documented
posture of every egregore deployment. It routes through
`night-market-change-control`. Do not shortcut it.

Preconditions, all required:

- [ ] P2 numbers met at the pre-registered thresholds, raw data
      committed.
- [ ] P3 attacks run, with Attack B either closed by a code-side check
      or formally accepted in the ADR with an owner.
- [ ] The promotion decision drafted as a numbered ADR in `docs/adr/`
      (next free number: ADR-0017 is the highest as of 2026-07-02),
      because this reverses a deliberate recorded default.

Implementation order (Iron Law: failing test first):

1. Branch per convention: `<topic>-<version>`, from `master`.
2. Turn the default's tests red first: in
   `plugins/egregore/tests/test_config.py`, change
   `test_pipeline_defaults` to expect `completion_integrity is True`
   and run it. Expected: 1 failure, proving the test binds the default.
3. Flip the default in `plugins/egregore/scripts/config.py`
   (`PipelineConfig.completion_integrity: bool = True`) and re-run:

   ```bash
   cd plugins/egregore
   uv run pytest tests/test_config.py tests/test_quality_gate.py -q
   ```

4. Update every document that states the default is off. Verified
   list as of 2026-07-02 (re-derive with the rg command in Provenance):
   `plugins/egregore/scripts/config.py` (comment),
   `plugins/egregore/tests/test_config.py` (comment),
   `plugins/egregore/agents/orchestrator.md`,
   `plugins/egregore/skills/quality-gate/SKILL.md`,
   `plugins/egregore/skills/summon/modules/pipeline.md`,
   `plugins/egregore/README.md`.
5. Add a CHANGELOG entry under `[Unreleased]` in Keep a Changelog
   format. Never rewrite historical entries.
6. Check the diff against the 200-line AI-commit cap (CONSTITUTION
   rule 2). The code flip is tiny, but the doc sweep plus ADR may
   exceed it: if so, the ADR itself is the required planning doc;
   reference it in the commit body.
7. Run the standard gates before committing (`make lint`,
   `make typecheck`, plugin tests) and follow the PR flow in
   `night-market-operations`.

Rollback: the flag remains user-overridable either way
(`{"pipeline": {"completion_integrity": false}}` in
`.egregore/config.json`), so promotion is reversible per-deployment
without a code change. State this in the ADR.
