"""TDD tests for SML-003 and SML-007 fixes in hookify.

SML-003: Narrow bare Exception catches in _load_bundled_rules and
_load_user_rules to (OSError, ValueError), so unexpected exceptions
propagate instead of being silently swallowed.

SML-007: Make get_bundled_rules_dir a public module-level function
(remove underscore prefix). The two get_rule_path functions in
config_loader.py (user rules) and install_rule.py (catalog rules)
were checked and are NOT near-identical -- they look up different
directories with different signatures. The shared concept is the
bundled rules directory computation, which is promoted to public API.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest


class TestSml003NarrowExceptions:
    """SML-003: bare Exception catch narrowed to (OSError, ValueError)."""

    def test_load_user_rules_propagates_runtime_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """RuntimeError from load_rule must propagate after narrowing.

        Before fix: bare except Exception swallows RuntimeError silently.
        After fix: RuntimeError propagates to the caller.
        """
        from hookify.core.config_loader import ConfigLoader

        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()
        # Create a dummy rule file so the loop body executes
        (rules_dir / "hookify.test-rule.local.md").write_text("placeholder")

        loader = ConfigLoader(user_rules_dir=rules_dir)

        def raise_runtime(path: Path, source: str = "user") -> None:
            raise RuntimeError("simulated unexpected error")

        monkeypatch.setattr(loader, "load_rule", raise_runtime)

        with pytest.raises(RuntimeError, match="simulated unexpected error"):
            loader._load_user_rules()

    def test_load_bundled_rules_propagates_runtime_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """RuntimeError from load_rule must propagate in bundled path too."""
        from hookify.core.config_loader import ConfigLoader

        bundled_dir = tmp_path / "rules"
        cat_dir = bundled_dir / "git"
        cat_dir.mkdir(parents=True)
        (cat_dir / "block-force-push.md").write_text("placeholder")

        loader = ConfigLoader()
        monkeypatch.setattr(loader, "bundled_rules_dir", bundled_dir)

        def raise_runtime(path: Path, source: str = "bundled") -> None:
            raise RuntimeError("bundled unexpected error")

        monkeypatch.setattr(loader, "load_rule", raise_runtime)

        with pytest.raises(RuntimeError, match="bundled unexpected error"):
            loader._load_bundled_rules()

    def test_load_user_rules_still_logs_oserror(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """OSError from load_rule is caught and logged as a warning."""
        from hookify.core.config_loader import ConfigLoader

        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()
        (rules_dir / "hookify.test-rule.local.md").write_text("placeholder")

        loader = ConfigLoader(user_rules_dir=rules_dir)

        def raise_oserror(path: Path, source: str = "user") -> None:
            raise OSError("file read failed")

        monkeypatch.setattr(loader, "load_rule", raise_oserror)

        with caplog.at_level(logging.WARNING):
            rules = loader._load_user_rules()

        assert rules == []
        assert any("file read failed" in r.message for r in caplog.records)

    def test_load_user_rules_still_logs_value_error(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """ValueError from load_rule is caught and logged as a warning."""
        from hookify.core.config_loader import ConfigLoader

        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()
        (rules_dir / "hookify.test-rule.local.md").write_text("placeholder")

        loader = ConfigLoader(user_rules_dir=rules_dir)

        def raise_value_error(path: Path, source: str = "user") -> None:
            raise ValueError("invalid YAML frontmatter")

        monkeypatch.setattr(loader, "load_rule", raise_value_error)

        with caplog.at_level(logging.WARNING):
            rules = loader._load_user_rules()

        assert rules == []
        assert any("invalid YAML frontmatter" in r.message for r in caplog.records)


class TestSml007PublicBundledRulesDir:
    """SML-007: get_bundled_rules_dir promoted to public API.

    The two get_rule_path functions (user path vs catalog path) were
    reviewed and are NOT duplicates -- they serve different purposes.
    The dedup that IS valid: the bundled rules directory computation is
    already in config_loader._get_bundled_rules_dir; promoting it to
    get_bundled_rules_dir (no underscore) exposes the shared concept.
    """

    def test_get_bundled_rules_dir_is_importable(self) -> None:
        """get_bundled_rules_dir must be importable without underscore prefix."""
        from hookify.core.config_loader import get_bundled_rules_dir

        result = get_bundled_rules_dir()
        assert isinstance(result, Path)

    def test_get_bundled_rules_dir_matches_skills_catalog(self) -> None:
        """Returned path must point to the rule-catalog/rules directory."""
        from hookify.core.config_loader import get_bundled_rules_dir

        result = get_bundled_rules_dir()
        assert result.parts[-3:] == ("skills", "rule-catalog", "rules")
