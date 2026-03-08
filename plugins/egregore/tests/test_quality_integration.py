"""Integration tests for quality stage pipeline flow."""

from __future__ import annotations

import textwrap
from pathlib import Path

from manifest import Manifest

from conventions import (
    calculate_verdict,
    check_conventions,
    conventions_for_step,
    filter_steps,
    load_codex,
)


class TestFullQualityFlow:
    """Integration: full quality stage from codex to verdict."""

    def test_code_review_catches_violations(self, tmp_path: Path) -> None:
        """Full flow: load codex, check files, get verdict."""
        # Load real codex
        codex_path = (
            Path(__file__).parent.parent / "conventions" / "codex.yml"
        )
        all_convs = load_codex(codex_path)

        # Filter to code-review step
        step_convs = conventions_for_step("code-review", all_convs)
        assert len(step_convs) >= 4  # C1-C5 minus paths/custom

        # Create a file with violations
        bad_file = tmp_path / "bad_module.py"
        bad_file.write_text(textwrap.dedent("""\
            import os

            def my_func():
                import json  # C1 violation
                return json.dumps({})

            x = 1  # noqa: E501  # C4 violation
        """))

        findings = check_conventions([bad_file], step_convs)
        verdict = calculate_verdict(findings)

        assert verdict.status == "fix-required"
        assert verdict.blocking_count >= 1  # C1 is blocking
        conv_ids = {f.convention_id for f in findings}
        assert "C1" in conv_ids

    def test_clean_code_passes(self, tmp_path: Path) -> None:
        """Clean code gets pass verdict."""
        codex_path = (
            Path(__file__).parent.parent / "conventions" / "codex.yml"
        )
        all_convs = load_codex(codex_path)
        step_convs = conventions_for_step("code-review", all_convs)

        # Filter to only grep-type conventions
        grep_convs = [c for c in step_convs if c.check_type == "grep"]

        clean_file = tmp_path / "clean.py"
        clean_file.write_text(textwrap.dedent("""\
            import os
            import json

            def my_func():
                return json.dumps({"cwd": os.getcwd()})
        """))

        findings = check_conventions([clean_file], grep_convs)
        verdict = calculate_verdict(findings)
        assert verdict.status == "pass"

    def test_quality_config_skip_works(self) -> None:
        """Work item can skip quality steps."""
        all_steps = [
            "code-review", "unbloat", "code-refinement",
            "update-tests", "update-docs",
        ]
        config = {"skip": ["unbloat", "code-refinement"]}
        steps = filter_steps(all_steps, config)
        assert steps == ["code-review", "update-tests", "update-docs"]

    def test_manifest_quality_config_roundtrip(
        self, tmp_path: Path
    ) -> None:
        """Quality config survives manifest save/load cycle."""
        m = Manifest(project_dir=str(tmp_path))
        item = m.add_work_item(
            source="prompt", source_ref="test quality"
        )
        item.quality_config = {"skip": ["unbloat"]}

        # Roundtrip through dict
        data = m.to_dict()
        m2 = Manifest.from_dict(data)
        item2 = m2.work_items[0]
        assert item2.quality_config == {"skip": ["unbloat"]}

    def test_verdict_records_to_manifest(self, tmp_path: Path) -> None:
        """Verdict decision format is compatible with manifest."""
        m = Manifest(project_dir=str(tmp_path))
        item = m.add_work_item(
            source="prompt", source_ref="test decisions"
        )

        verdict = calculate_verdict([])
        decision = verdict.to_decision("code-review")

        m.record_decision(
            item.id,
            step=decision["step"],
            chose=decision["chose"],
            why=decision["why"],
        )

        assert len(item.decisions) == 1
        assert item.decisions[0]["step"] == "code-review"
        assert item.decisions[0]["chose"] == "pass"

    def test_git_checkout_detected_in_skills(
        self, tmp_path: Path
    ) -> None:
        """C3 catches destructive git ops in markdown skill files."""
        codex_path = (
            Path(__file__).parent.parent / "conventions" / "codex.yml"
        )
        all_convs = load_codex(codex_path)
        c3_convs = [c for c in all_convs if c.id == "C3"]

        skill_md = tmp_path / "recovery.md"
        skill_md.write_text(
            "To fix: run `git checkout HEAD -- file.py`\n"
        )

        findings = check_conventions([skill_md], c3_convs)
        assert len(findings) == 1
        assert findings[0].convention_id == "C3"

    def test_hook_files_exempt_from_c1_and_c4(
        self, tmp_path: Path
    ) -> None:
        """Hook files are exempt from import and noqa rules."""
        codex_path = (
            Path(__file__).parent.parent / "conventions" / "codex.yml"
        )
        all_convs = load_codex(codex_path)

        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        hook = hooks_dir / "pre_tool.py"
        hook.write_text(textwrap.dedent("""\
            def run():
                import yaml  # noqa: F401
                return yaml.safe_load("{}")
        """))

        findings = check_conventions([hook], all_convs)
        # C1 and C4 should both be exempt for hook files
        conv_ids = {f.convention_id for f in findings}
        assert "C1" not in conv_ids
        assert "C4" not in conv_ids
