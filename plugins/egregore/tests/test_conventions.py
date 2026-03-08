"""Tests for convention codex loading and check engine."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from conventions import (
    Convention,
    check_conventions,
    load_codex,
)

# ── Codex loading tests (TASK-004) ──────────────────────


class TestLoadCodex:
    """Tests for load_codex() function."""

    def test_loads_valid_codex(self, tmp_path: Path) -> None:
        """Load a valid codex YAML and parse all conventions."""
        codex_path = tmp_path / "codex.yml"
        codex_path.write_text(textwrap.dedent("""\
            version: 1
            conventions:
              - id: C1
                name: test-convention
                description: A test convention
                check_type: grep
                grep_pattern: 'foo'
                file_globs: ["**/*.py"]
                exempt_paths: []
                severity: blocking
                enabled: true
        """))
        conventions = load_codex(codex_path)
        assert len(conventions) == 1
        assert conventions[0].id == "C1"
        assert conventions[0].name == "test-convention"
        assert conventions[0].check_type == "grep"
        assert conventions[0].severity == "blocking"

    def test_filters_disabled_conventions(self, tmp_path: Path) -> None:
        """Disabled conventions are excluded from the result."""
        codex_path = tmp_path / "codex.yml"
        codex_path.write_text(textwrap.dedent("""\
            version: 1
            conventions:
              - id: C1
                name: enabled-one
                description: Enabled
                check_type: grep
                grep_pattern: 'foo'
                severity: blocking
                enabled: true
              - id: C2
                name: disabled-one
                description: Disabled
                check_type: grep
                grep_pattern: 'bar'
                severity: warning
                enabled: false
        """))
        conventions = load_codex(codex_path)
        assert len(conventions) == 1
        assert conventions[0].id == "C1"

    def test_rejects_invalid_yaml(self, tmp_path: Path) -> None:
        """Invalid YAML raises a clear error."""
        codex_path = tmp_path / "codex.yml"
        codex_path.write_text("version: 1\nconventions: [[[invalid")
        with pytest.raises(ValueError, match="codex"):
            load_codex(codex_path)

    def test_rejects_missing_required_fields(self, tmp_path: Path) -> None:
        """Convention missing required fields raises error."""
        codex_path = tmp_path / "codex.yml"
        codex_path.write_text(textwrap.dedent("""\
            version: 1
            conventions:
              - id: C1
                name: missing-fields
        """))
        with pytest.raises(ValueError, match="check_type"):
            load_codex(codex_path)

    def test_handles_missing_file(self, tmp_path: Path) -> None:
        """Missing codex file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_codex(tmp_path / "nonexistent.yml")

    def test_loads_real_codex(self) -> None:
        """Load the actual project codex.yml."""
        codex_path = (
            Path(__file__).parent.parent / "conventions" / "codex.yml"
        )
        if not codex_path.exists():
            pytest.skip("codex.yml not found")
        conventions = load_codex(codex_path)
        assert len(conventions) >= 5
        ids = [c.id for c in conventions]
        assert "C1" in ids
        assert "C2" in ids
        assert "C3" in ids
        assert "C4" in ids
        assert "C5" in ids


# ── Check engine tests (TASK-005) ───────────────────────


class TestCheckConventions:
    """Tests for check_conventions() function."""

    @pytest.fixture()
    def c1_convention(self) -> Convention:
        """C1: top-level-imports convention."""
        return Convention(
            id="C1",
            name="top-level-imports",
            description="No function-level imports",
            check_type="grep",
            severity="blocking",
            enabled=True,
            grep_pattern=r"^\s+(import |from \S+ import )",
            file_globs=["**/*.py"],
            exempt_paths=["**/hooks/*.py", "**/conftest.py"],
        )

    @pytest.fixture()
    def c3_convention(self) -> Convention:
        """C3: no-destructive-git-ops convention."""
        return Convention(
            id="C3",
            name="no-destructive-git-ops",
            description="No git checkout or reset --hard",
            check_type="grep",
            severity="blocking",
            enabled=True,
            grep_pattern=r"git (checkout|reset\s+--hard|stash(?!\s+list))",
            file_globs=["**/*.py", "**/*.sh", "**/*.md"],
            exempt_paths=[],
        )

    @pytest.fixture()
    def c4_convention(self) -> Convention:
        """C4: no-noqa-suppression convention."""
        return Convention(
            id="C4",
            name="no-noqa-suppression",
            description="No noqa or type: ignore",
            check_type="grep",
            severity="warning",
            enabled=True,
            grep_pattern=r"(#\s*noqa|#\s*type:\s*ignore|#\s*pylint:\s*disable)",
            file_globs=["**/*.py"],
            exempt_paths=["**/hooks/*.py"],
        )

    def test_c1_detects_function_level_import(
        self, tmp_path: Path, c1_convention: Convention
    ) -> None:
        """C1: detect import inside a function body."""
        py_file = tmp_path / "bad.py"
        py_file.write_text(textwrap.dedent("""\
            def my_func():
                import os
                return os.getcwd()
        """))
        findings = check_conventions([py_file], [c1_convention])
        assert len(findings) == 1
        assert findings[0].convention_id == "C1"
        assert findings[0].line == 2
        assert findings[0].severity == "blocking"

    def test_c1_allows_top_level_import(
        self, tmp_path: Path, c1_convention: Convention
    ) -> None:
        """C1: top-level imports produce no findings."""
        py_file = tmp_path / "good.py"
        py_file.write_text(textwrap.dedent("""\
            import os

            def my_func():
                return os.getcwd()
        """))
        findings = check_conventions([py_file], [c1_convention])
        assert len(findings) == 0

    def test_c1_exempts_hook_files(
        self, tmp_path: Path, c1_convention: Convention
    ) -> None:
        """C1: hook files are exempt from import rules."""
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        hook_file = hooks_dir / "my_hook.py"
        hook_file.write_text(textwrap.dedent("""\
            def run():
                import yaml
                return yaml.safe_load("{}")
        """))
        findings = check_conventions([hook_file], [c1_convention])
        assert len(findings) == 0

    def test_c3_detects_git_checkout(
        self, tmp_path: Path, c3_convention: Convention
    ) -> None:
        """C3: detect git checkout in a script."""
        script = tmp_path / "deploy.sh"
        script.write_text("git checkout main\n")
        findings = check_conventions([script], [c3_convention])
        assert len(findings) == 1
        assert findings[0].convention_id == "C3"

    def test_c3_allows_git_restore(
        self, tmp_path: Path, c3_convention: Convention
    ) -> None:
        """C3: git restore is allowed."""
        script = tmp_path / "fix.sh"
        script.write_text("git restore --source HEAD -- file.py\n")
        findings = check_conventions([script], [c3_convention])
        assert len(findings) == 0

    def test_c3_detects_reset_hard(
        self, tmp_path: Path, c3_convention: Convention
    ) -> None:
        """C3: detect git reset --hard."""
        md = tmp_path / "guide.md"
        md.write_text("Run `git reset --hard HEAD` to clean up.\n")
        findings = check_conventions([md], [c3_convention])
        assert len(findings) == 1

    def test_c4_detects_noqa(
        self, tmp_path: Path, c4_convention: Convention
    ) -> None:
        """C4: detect noqa comment."""
        py_file = tmp_path / "messy.py"
        py_file.write_text("x = 1  # noqa: E501\n")
        findings = check_conventions([py_file], [c4_convention])
        assert len(findings) == 1
        assert findings[0].convention_id == "C4"
        assert findings[0].severity == "warning"

    def test_c4_detects_type_ignore(
        self, tmp_path: Path, c4_convention: Convention
    ) -> None:
        """C4: detect type: ignore comment."""
        py_file = tmp_path / "typed.py"
        py_file.write_text("x: int = 'nope'  # type: ignore\n")
        findings = check_conventions([py_file], [c4_convention])
        assert len(findings) == 1

    def test_c4_exempts_hook_files(
        self, tmp_path: Path, c4_convention: Convention
    ) -> None:
        """C4: hook files are exempt from noqa rules."""
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        hook = hooks_dir / "pre_tool.py"
        hook.write_text("import yaml  # noqa: F401\n")
        findings = check_conventions([hook], [c4_convention])
        assert len(findings) == 0

    def test_skips_non_matching_file_globs(
        self, tmp_path: Path, c1_convention: Convention
    ) -> None:
        """Conventions only check files matching their globs."""
        txt_file = tmp_path / "notes.txt"
        txt_file.write_text("    import os\n")
        findings = check_conventions([txt_file], [c1_convention])
        assert len(findings) == 0

    def test_idempotent_results(
        self, tmp_path: Path, c1_convention: Convention
    ) -> None:
        """Running checks twice produces identical results."""
        py_file = tmp_path / "bad.py"
        py_file.write_text("def f():\n    import os\n")
        r1 = check_conventions([py_file], [c1_convention])
        r2 = check_conventions([py_file], [c1_convention])
        assert len(r1) == len(r2)
        assert r1[0].convention_id == r2[0].convention_id
        assert r1[0].line == r2[0].line

    def test_multiple_violations_same_file(
        self, tmp_path: Path, c4_convention: Convention
    ) -> None:
        """Multiple violations in one file produce multiple findings."""
        py_file = tmp_path / "multi.py"
        py_file.write_text(
            "x = 1  # noqa\n"
            "y = 2  # type: ignore\n"
            "z = 3  # pylint: disable=C0114\n"
        )
        findings = check_conventions([py_file], [c4_convention])
        assert len(findings) == 3

    def test_multiple_conventions_checked(
        self,
        tmp_path: Path,
        c1_convention: Convention,
        c4_convention: Convention,
    ) -> None:
        """Multiple conventions checked against same file."""
        py_file = tmp_path / "double.py"
        py_file.write_text(
            "def f():\n"
            "    import os  # noqa\n"
        )
        findings = check_conventions(
            [py_file], [c1_convention, c4_convention]
        )
        ids = {f.convention_id for f in findings}
        assert "C1" in ids
        assert "C4" in ids

    def test_empty_file_no_findings(
        self, tmp_path: Path, c1_convention: Convention
    ) -> None:
        """Empty files produce no findings."""
        py_file = tmp_path / "empty.py"
        py_file.write_text("")
        findings = check_conventions([py_file], [c1_convention])
        assert len(findings) == 0


class TestCheckDocConsolidation:
    """Tests for C5 custom checker."""

    def test_detects_new_standalone_markdown(
        self, tmp_path: Path
    ) -> None:
        """C5: new markdown files outside skills/modules flagged."""
        from conventions import check_doc_consolidation

        new_md = tmp_path / "GUIDE.md"
        new_md.write_text("# Guide\nSome content\n")
        findings = check_doc_consolidation(
            [new_md], base_dir=tmp_path
        )
        assert len(findings) == 1
        assert findings[0].convention_id == "C5"

    def test_allows_skill_markdown(self, tmp_path: Path) -> None:
        """C5: markdown inside skills/ is allowed."""
        from conventions import check_doc_consolidation

        skills_dir = tmp_path / "skills" / "my-skill"
        skills_dir.mkdir(parents=True)
        skill_md = skills_dir / "SKILL.md"
        skill_md.write_text("# Skill\n")
        findings = check_doc_consolidation(
            [skill_md], base_dir=tmp_path
        )
        assert len(findings) == 0

    def test_allows_modules_markdown(self, tmp_path: Path) -> None:
        """C5: markdown inside modules/ is allowed."""
        from conventions import check_doc_consolidation

        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()
        mod_md = modules_dir / "feature.md"
        mod_md.write_text("# Module\n")
        findings = check_doc_consolidation(
            [mod_md], base_dir=tmp_path
        )
        assert len(findings) == 0

    def test_allows_readme(self, tmp_path: Path) -> None:
        """C5: README.md is always allowed."""
        from conventions import check_doc_consolidation

        readme = tmp_path / "README.md"
        readme.write_text("# Readme\n")
        findings = check_doc_consolidation(
            [readme], base_dir=tmp_path
        )
        assert len(findings) == 0
