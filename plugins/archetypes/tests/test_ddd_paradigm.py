"""Test: the domain-driven paradigm skill teaches DDD without ceremony.

DDD is modeling a business in the business's own language. Layering,
mapping, DTOs, and command objects are separable machinery a domain model
may or may not need. This suite guards the content that keeps those two
ideas apart, plus the one hard constraint (the IO boundary) that survives
regardless of how little ceremony a project adopts.

Every assertion anchors on a phrase unique to the paragraph it guards, so
deleting that paragraph turns the test red. This is a direct lesson from
the PR #612 review, where a content test passed the revert check only by
accident: its search terms appeared elsewhere in the file.

Feature: the DDD paradigm skill documents build-for-now and its limits.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
DDD_SKILL = PLUGIN_ROOT / "skills" / "architecture-paradigm-domain-driven" / "SKILL.md"
ROUTER_SKILL = PLUGIN_ROOT / "skills" / "architecture-paradigms" / "SKILL.md"


def _normalize(text: str) -> str:
    """Collapse whitespace runs so anchors survive an 80-column reflow.

    The repo wraps prose at 80 characters, so any anchor phrase long enough
    to be meaningful will eventually straddle a line break. Matching raw
    text would make these tests fail on a pure reflow, and would tempt an
    author to "fix" a red test by unwrapping a line.

    Collapsing whitespace keeps the property that matters: deleting the
    guarded paragraph still turns the test red. It only drops the
    dependency on where the line breaks happen to fall.

    Line-leading blockquote markers come off for the same reason. A quote
    wrapped at 80 columns puts a "> " in the middle of any anchor long
    enough to be unique, which would otherwise force an author to choose
    between a checkable anchor and a correctly wrapped quote.
    """
    without_quote_markers = re.sub(r"(?m)^>\s?", "", text)
    return re.sub(r"\s+", " ", without_quote_markers)


@pytest.fixture
def ddd_text() -> str:
    """The DDD paradigm SKILL.md body, whitespace-normalized."""
    assert DDD_SKILL.exists(), f"missing SKILL.md: {DDD_SKILL}"
    return _normalize(DDD_SKILL.read_text(encoding="utf-8"))


class TestDivergenceProtocol:
    """Feature: the DTO arrives on divergence, not in anticipation of it."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_divergence_protocol_states_its_trigger(self, ddd_text: str) -> None:
        """
        Scenario: a reader needs to know when to introduce a DTO
        Given the DDD paradigm skill
        When the divergence protocol is read
        Then it names the contract-shape trigger that justifies the split.
        """
        # Anchored on the full clause, not the bare phrase "moment of
        # divergence". That shorter phrase also appears in the Concrete
        # Components bullet for copy-constructor, so a test keyed to it
        # stays green even when this paragraph is deleted. That is exactly
        # the PR #612 defect, and the revert check caught it here.
        assert "arrives at the moment of divergence" in ddd_text, (
            "divergence protocol must state the DTO arrives at divergence"
        )
        assert "contract reasons" in ddd_text, (
            "divergence protocol must name the contract-shape trigger"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_divergence_protocol_states_its_move(self, ddd_text: str) -> None:
        """
        Scenario: a reader needs the mechanical step, not just the trigger
        Given the DDD paradigm skill
        When the divergence protocol is read
        Then the old object becomes the view DTO and a copy constructor maps.
        """
        assert "becomes the view DTO" in ddd_text, (
            "divergence protocol must state the old object becomes the view DTO"
        )
        assert "copy constructor" in ddd_text, (
            "divergence protocol must name the copy constructor as the mapper"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_shared_object_start_is_legitimate_not_debt(self, ddd_text: str) -> None:
        """
        Scenario: a reader fears that one shared object is technical debt
        Given the DDD paradigm skill
        When the build-for-now section is read
        Then passing one object through every layer is named a valid start.
        """
        assert "not technical debt" in ddd_text, (
            "build-for-now must state the shared-object start is not debt"
        )


class TestIOBoundaryRule:
    """Feature: the one hard constraint survives any amount of ceremony cut."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_io_boundary_rule_is_present(self, ddd_text: str) -> None:
        """
        Scenario: a reader strips ceremony and reaches a network call
        Given the DDD paradigm skill
        When the IO boundary section is read
        Then reusing a type across the boundary requires a field audit.
        """
        assert "across a network or other IO boundary" in ddd_text, (
            "IO boundary rule must forbid unvalidated cross-boundary type reuse"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_io_boundary_rule_is_marked_non_negotiable(self, ddd_text: str) -> None:
        """
        Scenario: a reader treats the boundary rule as another droppable rule
        Given the DDD paradigm skill
        When the IO boundary section is read
        Then the rule is explicitly the skill's one non-negotiable constraint.
        """
        assert "non-negotiable" in ddd_text, (
            "IO boundary rule must be stated as non-negotiable, unlike the rest"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_request_dto_justified_by_non_atomic_deploys(self, ddd_text: str) -> None:
        """
        Scenario: a reader asks whether a request DTO is ceremony
        Given the DDD paradigm skill
        When the request DTO rationale is read
        Then it is justified by rolling deploys, and named a deployment
        constraint rather than a DDD principle.
        """
        assert "do not deploy atomically" in ddd_text, (
            "request DTO must be justified by non-atomic deployment"
        )
        assert "deployment constraint, not a DDD principle" in ddd_text, (
            "request DTO rationale must disclaim itself as a DDD principle"
        )


class TestSharedTypeOptions:
    """Feature: shared-type options are offered with their costs stated."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_shared_base_class_is_offered(self, ddd_text: str) -> None:
        """
        Scenario: several contexts share a field core
        Given the DDD paradigm skill
        When the shared-type options are read
        Then a shared base class is offered as a legitimate option.
        """
        assert "Shared base class" in ddd_text, (
            "shared-type options must offer the shared base class"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_shared_base_class_coupling_cost_is_stated(self, ddd_text: str) -> None:
        """
        Scenario: a reader adopts the base class without seeing the trade
        Given the DDD paradigm skill
        When the shared base class option is read
        Then its coupling cost is stated plainly alongside the offer.

        The offer without the cost is the failure mode: inheritance across
        layers is the exact coupling the divergence protocol exists to avoid.
        """
        assert "inheritance couples the layers" in ddd_text, (
            "shared base class must state that inheritance couples the layers"
        )


class TestStranglerSequence:
    """Feature: decomposing an existing app is ordered, never a single pass."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_strangler_is_not_a_single_pass(self, ddd_text: str) -> None:
        """
        Scenario: a reader plans a big-bang domain refactor
        Given the DDD paradigm skill
        When the strangler section is read
        Then decomposing in one pass is ruled out.
        """
        assert "Never in one pass" in ddd_text, (
            "strangler section must rule out the single-pass refactor"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_strangler_orders_data_then_business_then_view(self, ddd_text: str) -> None:
        """
        Scenario: a reader starts a decomposition at the view layer
        Given the DDD paradigm skill
        When the strangler sequence is read
        Then data precedes business, which precedes view.

        Order is the whole content of this section, so the test asserts on
        position rather than mere presence.
        """
        data_at = ddd_text.find("**Data layer.**")
        business_at = ddd_text.find("**Business layer.**")
        view_at = ddd_text.find("**View layer.**")

        assert data_at != -1, "strangler sequence must name the data layer step"
        assert business_at != -1, "strangler sequence must name the business layer step"
        assert view_at != -1, "strangler sequence must name the view layer step"

        assert data_at < business_at < view_at, (
            "strangler sequence must order data, then business, then view "
            f"(found data={data_at}, business={business_at}, view={view_at})"
        )


class TestSkillContract:
    """Feature: the skill satisfies the repo's structural rules."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_has_exit_criteria(self, ddd_text: str) -> None:
        """
        Scenario: the model cannot tell when the skill is done
        Given the DDD paradigm skill
        When the body is read
        Then an Exit Criteria section is present.

        Required by .claude/rules/skill-exit-criteria.md.
        """
        assert "## Exit Criteria" in ddd_text, (
            "skill must have an Exit Criteria section (skill-exit-criteria rule)"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_separates_ddd_from_clean_architecture(self, ddd_text: str) -> None:
        """
        Scenario: a reader conflates DDD with mandatory layering
        Given the DDD paradigm skill
        When the 'What DDD is not' section is read
        Then Clean Architecture and mandatory layering are excluded from DDD.

        This is the skill's thesis. Without it the skill is just another
        layering guide.
        """
        assert "What DDD Is Not" in ddd_text, (
            "skill must carry a 'What DDD Is Not' section"
        )
        assert "Clean Architecture" in ddd_text, (
            "skill must name Clean Architecture as separable from DDD"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_router_lists_the_ddd_paradigm(self) -> None:
        """
        Scenario: a reader selects a paradigm from the router
        Given the architecture paradigm router
        When the available paradigms are read
        Then the DDD paradigm is listed and routable.
        """
        router_text = _normalize(ROUTER_SKILL.read_text(encoding="utf-8"))

        assert "architecture-paradigm-domain-driven" in router_text, (
            "router must list the DDD paradigm skill so it is reachable"
        )


class TestStrategicDesignIsTheCore:
    """Feature: the skill grounds its thesis in Evans's own correction.

    The skill's load-bearing claim is that the tactical building blocks are
    not the core of DDD. That claim is stronger sourced than asserted, and
    Evans made the correction himself. These tests guard the citation so a
    later edit cannot quietly drop the evidence and leave the assertion
    standing on the repo's own authority.
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_names_strategic_design_as_the_core(self, ddd_text: str) -> None:
        """
        Scenario: a reader doubts that ceremony is separable from DDD
        Given the DDD paradigm skill
        When the strategic-design section is read
        Then it states the building blocks are not the core of DDD.
        """
        assert (
            "really the core of DDD, whereas, in fact, it's really not" in ddd_text
        ), (
            "skill must carry Evans's correction that the building blocks are not the core of DDD"
        )
        assert "bounded contexts" in ddd_text, (
            "skill must name what the core actually is: subdomains and bounded contexts"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_evans_quote_carries_a_resolvable_source(self, ddd_text: str) -> None:
        """
        Scenario: a reader wants to check the quote against its source
        Given the DDD paradigm skill quotes Eric Evans
        When the attribution is read
        Then it names the episode and links it, so the citation resolves.

        Guards the repo's P0 hallucination rule. A quote attributed to a
        vague "IEEE interview" is not checkable; SE-Radio Episode 226 is.
        """
        assert "Episode 226" in ddd_text, (
            "Evans quote must name the specific episode it came from"
        )
        assert "GogQor9WG-c" in ddd_text, (
            "Evans quote must link its source so the citation resolves"
        )
