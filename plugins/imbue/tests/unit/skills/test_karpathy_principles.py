"""Tests for karpathy-principles skill structure and content.

Validates that the karpathy-principles skill exists with the expected
SKILL.md, four modules, source attribution reference, and that the five
existing skills carry cross-reference lines pointing at the new skill.

Derived from forrestchang/andrej-karpathy-skills (MIT) which itself
distills observations from Andrej Karpathy on common LLM coding
pitfalls.
"""

from __future__ import annotations

from pathlib import Path

import pytest


def _skill_root() -> Path:
    return Path(__file__).parents[3] / "skills" / "karpathy-principles"


class TestKarpathyPrinciplesStructure:
    """Feature: karpathy-principles skill has the expected files."""

    @pytest.fixture
    def skill_root(self) -> Path:
        return _skill_root()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_md_exists(self, skill_root: Path) -> None:
        """SKILL.md must exist at the skill root."""
        assert (skill_root / "SKILL.md").exists()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_required_modules_present(self, skill_root: Path) -> None:
        """All four modules and the attribution reference must exist."""
        required = [
            "modules/anti-patterns.md",
            "modules/senior-engineer-test.md",
            "modules/verifiable-goals.md",
            "modules/tradeoff-acknowledgment.md",
            "references/source-attribution.md",
        ]
        missing = [p for p in required if not (skill_root / p).exists()]
        assert not missing, f"missing files: {missing}"


class TestKarpathyPrinciplesFrontmatter:
    """Feature: SKILL.md frontmatter is well-formed."""

    @pytest.fixture
    def skill_md(self) -> str:
        return (_skill_root() / "SKILL.md").read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_required_frontmatter_fields(self, skill_md: str) -> None:
        """Frontmatter must declare name, description, version."""
        head = skill_md.split("---", 2)[1]
        for field in ("name:", "description:", "version:"):
            assert field in head, f"missing frontmatter field: {field}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_name_matches_directory(self, skill_md: str) -> None:
        """name field must equal karpathy-principles."""
        head = skill_md.split("---", 2)[1]
        assert "name: karpathy-principles" in head


class TestKarpathyPrinciplesContent:
    """Feature: Content covers the four principles and anti-patterns."""

    @pytest.fixture
    def skill_md(self) -> str:
        return (_skill_root() / "SKILL.md").read_text()

    @pytest.fixture
    def anti_patterns(self) -> str:
        return (_skill_root() / "modules" / "anti-patterns.md").read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_four_principles_present(self, skill_md: str) -> None:
        """SKILL.md must name all four principles."""
        for principle in (
            "Think Before Coding",
            "Simplicity First",
            "Surgical Changes",
            "Goal-Driven Execution",
        ):
            assert principle in skill_md, f"missing: {principle}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_eight_anti_pattern_cases(self, anti_patterns: str) -> None:
        """anti-patterns.md must cover the eight named drift rails."""
        cases = (
            "Hidden Assumptions",
            "Multiple Interpretations",
            "Strategy Pattern for One Function",
            "Speculative Features",
            "Drive-by Refactoring",
            "Style Drift",
            "Vague Success Criteria",
            "Multi-Step Plan Without Verification",
        )
        missing = [c for c in cases if c not in anti_patterns]
        assert not missing, f"missing cases: {missing}"


class TestKarpathyPrinciplesAttribution:
    """Feature: Source attribution cites both Karpathy and Forrest Chang."""

    @pytest.fixture
    def attribution(self) -> str:
        return (_skill_root() / "references" / "source-attribution.md").read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_cites_karpathy_tweet(self, attribution: str) -> None:
        assert "karpathy/status/2015883857489522876" in attribution

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_cites_forrest_chang_repo(self, attribution: str) -> None:
        assert "forrestchang/andrej-karpathy-skills" in attribution

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_declares_mit_license(self, attribution: str) -> None:
        assert "MIT" in attribution


class TestCrossReferencesInExistingSkills:
    """Feature: Existing skills point at the new entry-point skill."""

    @pytest.fixture
    def repo_root(self) -> Path:
        return Path(__file__).parents[5]

    @pytest.mark.parametrize(
        "rel_path",
        [
            "plugins/imbue/skills/scope-guard/SKILL.md",
            "plugins/imbue/skills/proof-of-work/SKILL.md",
            "plugins/imbue/skills/rigorous-reasoning/SKILL.md",
            "plugins/leyline/skills/additive-bias-defense/SKILL.md",
            "plugins/conserve/skills/code-quality-principles/SKILL.md",
        ],
    )
    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_references_karpathy_principles(
        self, repo_root: Path, rel_path: str
    ) -> None:
        """Each existing skill must mention karpathy-principles."""
        text = (repo_root / rel_path).read_text()
        assert "karpathy-principles" in text, (
            f"no karpathy-principles cross-reference in {rel_path}"
        )


class TestPluginManifestRegistration:
    """Feature: imbue plugin.json registers the new skill."""

    @pytest.fixture
    def manifest(self) -> str:
        manifest_path = Path(__file__).parents[3] / ".claude-plugin" / "plugin.json"
        return manifest_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_registered_in_manifest(self, manifest: str) -> None:
        assert "karpathy-principles" in manifest
