"""Integration tests for quality stage pipeline flow."""

from __future__ import annotations

import textwrap
from pathlib import Path

from conventions import (
    check_conventions,
    load_codex,
)
from manifest import Manifest


class TestFullQualityFlow:
    """Integration: full quality stage from codex to verdict."""

    def test_manifest_quality_config_roundtrip(self, tmp_path: Path) -> None:
        """Quality config survives manifest save/load cycle."""
        m = Manifest(project_dir=str(tmp_path))
        item = m.add_work_item(source="prompt", source_ref="test quality")
        item.quality_config = {"skip": ["unbloat"]}

        # Roundtrip through dict
        data = m.to_dict()
        m2 = Manifest.from_dict(data)
        item2 = m2.work_items[0]
        assert item2.quality_config == {"skip": ["unbloat"]}

    def test_git_checkout_detected_in_skills(self, tmp_path: Path) -> None:
        """C3 catches destructive git ops in markdown skill files."""
        codex_path = Path(__file__).parent.parent / "conventions" / "codex.yml"
        all_convs = load_codex(codex_path)
        c3_convs = [c for c in all_convs if c.id == "C3"]

        skill_md = tmp_path / "recovery.md"
        skill_md.write_text("To fix: run `git checkout HEAD -- file.py`\n")

        findings = check_conventions([skill_md], c3_convs)
        assert len(findings) == 1
        assert findings[0].convention_id == "C3"

    def test_hook_files_exempt_from_c1_and_c4(self, tmp_path: Path) -> None:
        """Hook files are exempt from import and noqa rules."""
        codex_path = Path(__file__).parent.parent / "conventions" / "codex.yml"
        all_convs = load_codex(codex_path)

        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        hook = hooks_dir / "pre_tool.py"
        hook.write_text(
            textwrap.dedent("""\
            def run():
                import yaml
                return yaml.safe_load("{}")
        """)
        )

        findings = check_conventions([hook], all_convs)
        # C1 and C4 should both be exempt for hook files
        conv_ids = {f.convention_id for f in findings}
        assert "C1" not in conv_ids
        assert "C4" not in conv_ids
