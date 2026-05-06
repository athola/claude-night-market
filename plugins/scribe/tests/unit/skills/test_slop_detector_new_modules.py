"""BDD tests for new slop-detector modules added per AI Slop Playbook.

Feature: Slop Detector Covers Identity, Hallucination, Stub,
  Evidence, Anti-Goals, Workflow, and Empirical-Baseline
  As a documentation reviewer
  I want the slop-detector skill to enforce the full 2025-26
  research playbook, not just sentence-level vocabulary
  So that identity leaks, hallucinations, and unverified
  claims cannot ship.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

SKILL_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent / "skills" / "slop-detector"
)
SKILL_FILE = SKILL_DIR / "SKILL.md"
MODULES_DIR = SKILL_DIR / "modules"

NEW_MODULES = [
    "identity-and-voice-leaks",
    "hallucination-detection",
    "stub-and-deferral",
    "evidence-backed-claims",
    "anti-goals",
    "cleanup-workflow",
    "empirical-baseline",
]


def _parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from a SKILL.md file."""
    if not content.startswith("---"):
        return {}
    end = content.index("---", 3)
    return yaml.safe_load(content[3:end])


class TestNewModulesExist:
    """Feature: All seven new modules exist on disk."""

    @pytest.mark.unit
    @pytest.mark.parametrize("module", NEW_MODULES)
    def test_module_file_exists(self, module: str) -> None:
        """Each new module must exist as a .md file."""
        path = MODULES_DIR / f"{module}.md"
        assert path.exists(), f"Expected module at {path}"

    @pytest.mark.unit
    @pytest.mark.parametrize("module", NEW_MODULES)
    def test_module_has_frontmatter(self, module: str) -> None:
        """Each new module must begin with YAML frontmatter."""
        text = (MODULES_DIR / f"{module}.md").read_text()
        assert text.startswith("---"), f"{module}.md must begin with YAML frontmatter"

    @pytest.mark.unit
    @pytest.mark.parametrize("module", NEW_MODULES)
    def test_frontmatter_lists_module_name(self, module: str) -> None:
        """Frontmatter must declare the module name."""
        text = (MODULES_DIR / f"{module}.md").read_text()
        end = text.index("---", 3)
        fm = yaml.safe_load(text[3:end])
        assert fm.get("module") == module, f"Frontmatter `module:` must be '{module}'"


class TestSkillMdWiresInNewModules:
    """Feature: SKILL.md frontmatter and body reference the new modules."""

    @pytest.fixture
    def skill_text(self) -> str:
        return SKILL_FILE.read_text()

    @pytest.mark.unit
    @pytest.mark.parametrize("module", NEW_MODULES)
    def test_frontmatter_lists_new_module(self, skill_text: str, module: str) -> None:
        """Each new module must appear in frontmatter `modules:` list."""
        fm = _parse_frontmatter(skill_text)
        modules = fm.get("modules", [])
        assert module in modules, f"slop-detector frontmatter must list '{module}'"

    @pytest.mark.unit
    @pytest.mark.parametrize("module", NEW_MODULES)
    def test_body_references_new_module(self, skill_text: str, module: str) -> None:
        """SKILL.md body must reference each new module by name."""
        assert module in skill_text, (
            f"SKILL.md body must reference '{module}' so readers know to load it"
        )


class TestIdentityLeakModule:
    """Feature: identity-and-voice-leaks declares P0 patterns."""

    @pytest.fixture
    def text(self) -> str:
        return (MODULES_DIR / "identity-and-voice-leaks.md").read_text()

    @pytest.mark.unit
    def test_module_lists_llm_self_reference(self, text: str) -> None:
        """Module must list the canonical LLM self-reference patterns."""
        assert "As a large language model" in text
        assert "training cutoff" in text or "knowledge cutoff" in text

    @pytest.mark.unit
    def test_module_lists_conversational_artifacts(self, text: str) -> None:
        """Module must list conversational artifacts (Hope this helps, etc.)."""
        text_lower = text.lower()
        assert "hope this helps" in text_lower
        assert "great question" in text_lower

    @pytest.mark.unit
    def test_module_lists_self_narration(self, text: str) -> None:
        """Module must cover self-narration of structure."""
        text_lower = text.lower()
        assert "let's dive into" in text_lower or ("in this section" in text_lower)

    @pytest.mark.unit
    def test_module_marks_identity_leaks_as_p0(self, text: str) -> None:
        """Identity leaks must be marked critical/P0/categorical."""
        text_lower = text.lower()
        assert (
            "p0" in text_lower
            or "critical" in text_lower
            or ("categorical" in text_lower)
        )


class TestHallucinationModule:
    """Feature: hallucination-detection covers phantom-reference classes."""

    @pytest.fixture
    def text(self) -> str:
        return (MODULES_DIR / "hallucination-detection.md").read_text()

    @pytest.mark.unit
    def test_covers_phantom_imports(self, text: str) -> None:
        """Module must cover phantom imports/dependencies."""
        text_lower = text.lower()
        assert "phantom" in text_lower or "hallucinated" in text_lower

    @pytest.mark.unit
    def test_covers_dead_urls(self, text: str) -> None:
        """Module must cover dead-URL detection."""
        text_lower = text.lower()
        assert "url" in text_lower and ("dead" in text_lower or "404" in text_lower)

    @pytest.mark.unit
    def test_covers_slopsquatting(self, text: str) -> None:
        """Module must reference the slopsquatting attack class."""
        assert "slopsquatting" in text.lower(), (
            "Module must name the slopsquatting class explicitly"
        )

    @pytest.mark.unit
    def test_covers_model_specific_calibration(self, text: str) -> None:
        """Module must address model-specific (GPT vs. Claude) patterns."""
        text_lower = text.lower()
        assert "gpt" in text_lower and "claude" in text_lower


class TestStubAndDeferralModule:
    """Feature: stub-and-deferral covers TODO-class patterns."""

    @pytest.fixture
    def text(self) -> str:
        return (MODULES_DIR / "stub-and-deferral.md").read_text()

    @pytest.mark.unit
    def test_covers_todo_patterns(self, text: str) -> None:
        """Module must cover TODO/FIXME/XXX/HACK."""
        for token in ["TODO", "FIXME", "XXX", "HACK"]:
            assert token in text, f"Module must list {token}"

    @pytest.mark.unit
    def test_covers_hedging_language(self, text: str) -> None:
        """Module must cover 'for now' / 'should work' / 'placeholder'."""
        text_lower = text.lower()
        assert "for now" in text_lower
        assert "placeholder" in text_lower or "stub" in text_lower

    @pytest.mark.unit
    def test_requires_tracked_issue_or_delete(self, text: str) -> None:
        """Module must state the resolve/track/delete trichotomy."""
        text_lower = text.lower()
        assert (
            "tracked" in text_lower or "linked" in text_lower or ("issue" in text_lower)
        )


class TestEvidenceBackedClaimsModule:
    """Feature: evidence-backed-claims operationalizes the README rule."""

    @pytest.fixture
    def text(self) -> str:
        return (MODULES_DIR / "evidence-backed-claims.md").read_text()

    @pytest.mark.unit
    def test_covers_production_ready_claim(self, text: str) -> None:
        """Module must cover the 'production-ready' claim."""
        text_lower = text.lower()
        assert "production-ready" in text_lower or ("production ready" in text_lower)

    @pytest.mark.unit
    def test_covers_fast_blazing_fast_claim(self, text: str) -> None:
        """Module must cover the 'fast'/'blazing-fast' claim."""
        text_lower = text.lower()
        assert "blazing" in text_lower or "fast" in text_lower
        assert "bench" in text_lower

    @pytest.mark.unit
    def test_provides_required_evidence_table(self, text: str) -> None:
        """Module must contain a claim → required-evidence table."""
        assert "Required evidence" in text or ("required-evidence" in text.lower())


class TestAntiGoalsModule:
    """Feature: anti-goals lists the cleanup safety rails."""

    @pytest.fixture
    def text(self) -> str:
        return (MODULES_DIR / "anti-goals.md").read_text()

    @pytest.mark.unit
    def test_protects_safety_comments(self, text: str) -> None:
        """Module must protect SAFETY/INVARIANT comment classes."""
        assert "SAFETY" in text
        assert "INVARIANT" in text or "Invariant" in text

    @pytest.mark.unit
    def test_protects_generated_and_vendored_code(self, text: str) -> None:
        """Module must protect generated code and vendored directories."""
        text_lower = text.lower()
        assert "generated" in text_lower
        assert (
            "vendor" in text_lower
            or "third_party" in text_lower
            or ("vendored" in text_lower)
        )

    @pytest.mark.unit
    def test_addresses_low_confidence_findings(self, text: str) -> None:
        """Module must address the low-confidence-finding policy."""
        text_lower = text.lower()
        assert "low" in text_lower and ("confidence" in text_lower)


class TestCleanupWorkflowModule:
    """Feature: cleanup-workflow defines the multi-pass methodology."""

    @pytest.fixture
    def text(self) -> str:
        return (MODULES_DIR / "cleanup-workflow.md").read_text()

    @pytest.mark.unit
    def test_includes_pre_slop_pass_zero(self, text: str) -> None:
        """Pass 0 (pre-slop / secrets sweep) must be defined first."""
        assert "Pass 0" in text

    @pytest.mark.unit
    def test_lists_at_least_ten_passes(self, text: str) -> None:
        """Workflow must define at least passes 0 through 10."""
        for pass_num in range(0, 11):
            assert f"Pass {pass_num}" in text, f"Workflow must define Pass {pass_num}"

    @pytest.mark.unit
    def test_states_one_pass_per_commit_rule(self, text: str) -> None:
        """The 'one pass per commit' rule must be explicit."""
        text_lower = text.lower()
        assert "one pass per commit" in text_lower or ("commit between" in text_lower)


class TestEmpiricalBaselineModule:
    """Feature: empirical-baseline cites 2025-26 research."""

    @pytest.fixture
    def text(self) -> str:
        return (MODULES_DIR / "empirical-baseline.md").read_text()

    @pytest.mark.unit
    def test_cites_coderabbit_data(self, text: str) -> None:
        """Module must cite the CodeRabbit Dec 2025 ratios."""
        text_lower = text.lower()
        assert "coderabbit" in text_lower

    @pytest.mark.unit
    def test_cites_metr_study(self, text: str) -> None:
        """Module must cite the METR productivity-paradox study."""
        text_lower = text.lower()
        assert "metr" in text_lower

    @pytest.mark.unit
    def test_addresses_fabricates_vs_omits(self, text: str) -> None:
        """Module must contrast fabrication (GPT) vs. omission (Claude)."""
        text_lower = text.lower()
        assert "fabricate" in text_lower or "fabricates" in text_lower
        assert "omit" in text_lower or "omits" in text_lower

    @pytest.mark.unit
    def test_includes_currency_caveat(self, text: str) -> None:
        """Module must caveat that the numbers will date."""
        text_lower = text.lower()
        assert (
            "currency" in text_lower
            or "re-validate" in text_lower
            or ("date" in text_lower)
        )


class TestRuleFileWiresInNewLayers:
    """Feature: project rule references the three-layer model."""

    @pytest.fixture
    def rule_text(self) -> str:
        rule = (
            Path(__file__).resolve().parents[5]
            / ".claude"
            / "rules"
            / "slop-scan-for-docs.md"
        )
        return rule.read_text()

    @pytest.mark.unit
    def test_rule_mentions_p0_layer(self, rule_text: str) -> None:
        """Rule must declare the P0 critical layer."""
        text_lower = rule_text.lower()
        assert "p0" in text_lower or "critical" in text_lower

    @pytest.mark.unit
    def test_rule_mentions_identity_leaks(self, rule_text: str) -> None:
        """Rule must point readers at identity-leak detection."""
        text_lower = rule_text.lower()
        assert "identity" in text_lower and "leak" in text_lower

    @pytest.mark.unit
    def test_rule_mentions_hallucination_detection(self, rule_text: str) -> None:
        """Rule must point readers at hallucination detection."""
        text_lower = rule_text.lower()
        assert "hallucination" in text_lower

    @pytest.mark.unit
    def test_rule_mentions_evidence_backed_claims(self, rule_text: str) -> None:
        """Rule must point readers at evidence-backed-claims."""
        text_lower = rule_text.lower()
        assert "evidence" in text_lower and "claim" in text_lower
