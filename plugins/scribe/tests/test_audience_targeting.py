"""Test: audience targeting is declared, asked for, and wired everywhere.

A document that serves everyone serves no one. The audience-targeting
module is the pattern source for that claim: it names three reader tiers,
gives the cut test that follows from a declared tier, and says where cut
content goes instead of the bin.

These are contract tests over prose, following the precedent in
``pensive/tests/skills/test_ceremony_audit.py``. Each assertion anchors on
a clause unique to the passage it guards, so deleting that passage turns
the test red. Whitespace is normalized because the repository reflows
prose at 80 columns and a pure reflow must not fail a test.

The wiring assertions matter as much as the module ones. A pattern source
no surface consults is the shared-utility failure the repo already has a
rule about.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGINS = REPO_ROOT / "plugins"

SLOP_DETECTOR = PLUGINS / "scribe" / "skills" / "slop-detector"
AUDIENCE_MODULE = SLOP_DETECTOR / "modules" / "audience-targeting.md"
DOCUMENT_ECONOMY = SLOP_DETECTOR / "modules" / "document-economy.md"
SLOP_DETECTOR_SKILL = SLOP_DETECTOR / "SKILL.md"

DOC_GENERATOR = PLUGINS / "scribe" / "skills" / "doc-generator" / "SKILL.md"
TECH_TUTORIAL = PLUGINS / "scribe" / "skills" / "tech-tutorial" / "SKILL.md"
DOC_UPDATES = PLUGINS / "sanctum" / "skills" / "doc-updates" / "SKILL.md"
UPDATE_README = PLUGINS / "sanctum" / "skills" / "update-readme" / "SKILL.md"
DOC_CONSOLIDATION = PLUGINS / "sanctum" / "skills" / "doc-consolidation" / "SKILL.md"
SKILL_AUTHORING = PLUGINS / "abstract" / "skills" / "skill-authoring" / "SKILL.md"
PROJECT_BRAINSTORMING = (
    PLUGINS / "attune" / "skills" / "project-brainstorming" / "SKILL.md"
)
PROJECT_SPECIFICATION = (
    PLUGINS / "attune" / "skills" / "project-specification" / "SKILL.md"
)
DOC_SWEEP_WORKFLOW = PLUGINS / "scribe" / "workflows" / "doc-sweep.js"
SLOP_RULE = REPO_ROOT / ".claude" / "rules" / "slop-scan-for-docs.md"

# Surfaces that must consult the module, and must say when they stop.
CONSUMER_SKILLS = (
    DOC_GENERATOR,
    TECH_TUTORIAL,
    DOC_UPDATES,
    UPDATE_README,
    DOC_CONSOLIDATION,
    SKILL_AUTHORING,
    PROJECT_BRAINSTORMING,
    PROJECT_SPECIFICATION,
)


def _normalize(text: str) -> str:
    """Collapse whitespace runs so anchors survive an 80-column reflow.

    Deleting a guarded paragraph still turns the test red. Only the
    dependency on where line breaks happen to fall is dropped.
    """
    return re.sub(r"\s+", " ", text)


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return _normalize(path.read_text(encoding="utf-8"))


@pytest.fixture
def module_text() -> str:
    """The audience-targeting module body, whitespace-normalized."""
    return _read(AUDIENCE_MODULE)


class TestTierTaxonomy:
    """Feature: three named tiers, each with the cut rule it implies."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_newcomer_tier_assumes_no_project_context(self, module_text: str) -> None:
        """
        Scenario: a reader has never seen this project
        Given the audience-targeting module
        When the tier table is read
        Then the newcomer tier assumes no project context and cuts
             rationale that a first reader cannot use.
        """
        assert "`newcomer`" in module_text
        assert "never seen this project" in module_text, (
            "the newcomer tier must be defined by zero project context"
        )
        assert "one path that works" in module_text, (
            "the newcomer cut rule must keep a single working path"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_practitioner_tier_knows_domain_not_repo(self, module_text: str) -> None:
        """
        Scenario: a reader knows the domain but not this repository
        Given the audience-targeting module
        When the tier table is read
        Then the practitioner tier cuts general-domain teaching and keeps
             the repo-specific facts the reader cannot derive.
        """
        assert "`practitioner`" in module_text
        assert "not this repository" in module_text, (
            "the practitioner tier must be defined against repo knowledge"
        )
        assert "cannot derive" in module_text, (
            "the practitioner cut rule must keep only non-derivable facts"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_expert_tier_keeps_the_novel_claim(self, module_text: str) -> None:
        """
        Scenario: a reader already knows this material
        Given the audience-targeting module
        When the tier table is read
        Then the expert tier cuts what the reader can derive and keeps the
             novel claim, the numbers, and the edge cases.
        """
        assert "`expert`" in module_text
        assert "already familiar" in module_text, (
            "the expert tier must be defined by existing familiarity"
        )
        assert "novel claim" in module_text, (
            "the expert cut rule must keep the claim the reader lacks"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_persona_escape_hatch_exists(self, module_text: str) -> None:
        """
        Scenario: no listed tier fits the real reader
        Given the audience-targeting module
        When the taxonomy is read
        Then a free-form persona may be declared instead of a tier.
        """
        assert "`persona`" in module_text, (
            "a free-form persona must be available when no tier fits"
        )


class TestAskDoNotGuess:
    """Feature: an unstated audience is asked for, not assumed."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_unstated_tier_is_asked_for(self, module_text: str) -> None:
        """
        Scenario: a generation request omits the audience
        Given the audience-targeting module
        When the declaration rule is read
        Then the tier is asked for rather than guessed.
        """
        assert "ask, do not guess" in module_text, (
            "an unstated tier must trigger a question, not an assumption"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_socratic_question_set_is_present(self, module_text: str) -> None:
        """
        Scenario: the engineer has not thought about the reader
        Given the audience-targeting module
        When the socratic question set is read
        Then it asks who the reader is, what they can do afterward, and
             what an expert would skip.
        """
        assert "Socratic" in module_text
        assert "what do they already know" in module_text, (
            "the question set must establish prior knowledge"
        )
        assert "could not do before" in module_text, (
            "the question set must establish the capability delta"
        )
        assert "would an expert skip" in module_text, (
            "the question set must surface extraction candidates"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_strength_is_default_not_invariant(self, module_text: str) -> None:
        """
        Scenario: a session weighs how hard this binds
        Given the audience-targeting module
        When the strength is read
        Then it is a Default in the bounded-autonomy budget, and no
             recorded failure justifies blocking a draft.
        """
        assert "bounded-autonomy" in module_text
        assert "Default, not an invariant" in module_text, (
            "strength must be stated as Default so a draft is never blocked"
        )


class TestCutTest:
    """Feature: four verdicts, so cutting is never the only option."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_four_verdicts_are_named(self, module_text: str) -> None:
        """
        Scenario: a passage is weighed against the declared tier
        Given the audience-targeting module
        When the cut test is read
        Then keep, link, extract, and delete are each defined.
        """
        for verdict in ("Keep", "Link", "Extract", "Delete"):
            assert f"**{verdict}**" in module_text, (
                f"the cut test must define the {verdict.lower()} verdict"
            )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_keep_is_bounded_by_before_they_can_act(self, module_text: str) -> None:
        """
        Scenario: a passage is useful but not yet needed
        Given the audience-targeting module
        When the keep verdict is read
        Then keep is bounded to what the reader needs before acting, and
             merely-eventual material is linked instead.
        """
        assert "before they can act" in module_text, (
            "keep must be bounded to pre-action need"
        )
        assert "eventually but not now" in module_text, (
            "material needed later must be linked, not kept inline"
        )


class TestExtractionProtocol:
    """Feature: expert content moves to a deep dive, it is not binned."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skills_extract_to_modules(self, module_text: str) -> None:
        """
        Scenario: a skill hub carries expert-only material
        Given the audience-targeting module
        When the extraction protocol is read
        Then skills extract to modules/ and update the frontmatter list.
        """
        assert "`modules/`" in module_text, (
            "skills must extract into their existing module directory"
        )
        assert "progressive_loading" in module_text, (
            "extraction must preserve the progressive loading contract"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_repo_docs_extract_to_deep_dive(self, module_text: str) -> None:
        """
        Scenario: a repo document carries expert-only material
        Given the audience-targeting module
        When the extraction protocol is read
        Then it extracts to docs/deep-dive/ and is linked from the lead.
        """
        assert "docs/deep-dive/" in module_text, (
            "repo docs must extract to the deep-dive directory"
        )
        assert "linked from the lead" in module_text, (
            "an extracted deep dive must be reachable from the parent lead"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_extraction_precedes_deletion(self, module_text: str) -> None:
        """
        Scenario: content fails the tier but is still true and useful
        Given the audience-targeting module
        When the extraction protocol is read
        Then content is moved and linked rather than deleted to hit a tier.
        """
        assert "Never delete to hit a tier" in module_text, (
            "hitting a tier must never be a reason to destroy content"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_deep_dive_names_its_own_reader(self, module_text: str) -> None:
        """
        Scenario: a deep dive is created
        Given the audience-targeting module
        When the extraction protocol is read
        Then the deep dive declares its own tier, so extraction cannot be
             used to dodge the rule.
        """
        assert "declares its own tier" in module_text, (
            "a deep dive must itself be audience-targeted"
        )


class TestCreativeCarveOut:
    """Feature: creative cycles are named out of scope, and say why."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_creative_surfaces_are_excluded(self, module_text: str) -> None:
        """
        Scenario: a voice or narrative skill generates text
        Given the audience-targeting module
        When the scope boundary is read
        Then the voice skills, session-to-post, and fiction patterns are
             excluded by name.
        """
        assert "voice-" in module_text
        assert "session-to-post" in module_text, (
            "narrative post generation must be out of scope"
        )
        assert "fiction-patterns" in module_text, (
            "fiction patterns must be out of scope"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_carve_out_states_its_reason(self, module_text: str) -> None:
        """
        Scenario: a reader asks why creative work is exempt
        Given the audience-targeting module
        When the scope boundary is read
        Then it says the digressions are the point, so the cut test would
             delete the work.
        """
        assert "digressions are the point" in module_text, (
            "the carve-out must state why the cut test does not transfer"
        )


class TestWiring:
    """Feature: every consuming surface reaches the pattern source."""

    @pytest.mark.bdd
    @pytest.mark.unit
    @pytest.mark.parametrize("skill_path", CONSUMER_SKILLS, ids=lambda p: p.parent.name)
    def test_consumer_references_the_module(self, skill_path: Path) -> None:
        """
        Scenario: a documentation surface drafts or rewrites prose
        Given a consuming skill
        When its body is read
        Then it names the audience-targeting module.
        """
        assert "audience-targeting" in _read(skill_path), (
            f"{skill_path.parent.name} must consult the audience module"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    @pytest.mark.parametrize("skill_path", CONSUMER_SKILLS, ids=lambda p: p.parent.name)
    def test_consumer_has_exit_criteria(self, skill_path: Path) -> None:
        """
        Scenario: a skill is edited
        Given a consuming skill
        When its body is read
        Then it carries an Exit Criteria section, per the repo rule.
        """
        assert "## Exit Criteria" in _read(skill_path), (
            f"{skill_path.parent.name} must carry Exit Criteria"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_slop_detector_registers_the_module(self) -> None:
        """
        Scenario: the slop detector loads its modules
        Given the slop-detector skill
        When the module list is read
        Then audience-targeting is registered so it can be loaded.
        """
        assert "audience-targeting" in _read(SLOP_DETECTOR_SKILL), (
            "the module must be registered on its own skill"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_document_economy_adds_audience_fit_check(self) -> None:
        """
        Scenario: a document is scored for economy
        Given the document-economy module
        When the checks are read
        Then audience fit is a scored check that defers to the module.
        """
        economy = _read(DOCUMENT_ECONOMY)
        assert "Check 4: Audience fit" in economy, (
            "document economy must score audience fit, not only weight"
        )
        assert "audience-targeting" in economy, (
            "document economy must defer to the pattern source"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_document_economy_rubric_covers_four_checks(self) -> None:
        """
        Scenario: the economy score is computed
        Given the document-economy module
        When the rubric is read
        Then the denominator reflects four checks rather than three.
        """
        economy = _read(DOCUMENT_ECONOMY)
        assert "sum / 8" in economy, (
            "adding a fourth check must move the rubric denominator to 8"
        )
        assert "sum / 6" not in economy, (
            "the stale three-check denominator must not survive the edit"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_repo_rule_carries_the_audience_layer(self) -> None:
        """
        Scenario: any session writes markdown in this repository
        Given the slop-scan rule loaded into every session
        When it is read
        Then it names the audience layer and points at the module rather
             than restating it.
        """
        rule = _read(SLOP_RULE)
        assert "audience" in rule.lower()
        assert "audience-targeting" in rule, (
            "the repo rule must point at the pattern source"
        )
        assert "docs/deep-dive/" in rule, (
            "the repo rule must name the extraction destination"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_doc_generator_request_template_has_the_field(self) -> None:
        """
        Scenario: a generation request is opened
        Given the doc-generator skill
        When the request template is read
        Then it carries an audience tier field.
        """
        generator = _read(DOC_GENERATOR)
        assert "**Audience tier**" in generator, (
            "the generation request must capture the tier explicitly"
        )
        assert "ask, do not guess" in generator, (
            "doc-generator must ask when the tier is unstated"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_doc_sweep_workflow_reviews_audience_fit(self) -> None:
        """
        Scenario: the doc-sweep workflow reviews a batch of documents
        Given the workflow script
        When its review dimensions are read
        Then audience fit is one of them.
        """
        workflow = _read(DOC_SWEEP_WORKFLOW)
        assert "audience" in workflow.lower(), (
            "the doc-sweep workflow must review audience fit"
        )


class TestNoPatternClaim:
    """Feature: the module does not pretend to be regex-detectable."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_states_it_is_not_a_regex_check(self, module_text: str) -> None:
        """
        Scenario: an author looks for the en.yaml section behind this
        Given the audience-targeting module
        When its detection note is read
        Then it says no regex can decide audience fit, which is why
             en.yaml carries nothing for it.
        """
        assert "no regex" in module_text.lower(), (
            "the module must state that audience fit is not regex-decidable"
        )
        assert "en.yaml" in module_text, (
            "the module must explain its absence from the pattern data"
        )
