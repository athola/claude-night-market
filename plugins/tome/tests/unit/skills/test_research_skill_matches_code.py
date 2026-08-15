"""The operator instructions must describe the pipeline that exists.

Feature: SKILL.md and the frontier code do not drift apart.

As an operator reading the research skill
I want its account of the verdict to match what the code does
So that I am not told to expect a result the pipeline stopped producing

SKILL.md told operators to expect INCONCLUSIVE on every run with a gap,
"until canary targets exist". The targets landed and the paragraph did
not, so the instructions spent that window teaching operators to read a
real signal as a known placeholder. Nothing tied the prose to the code,
so nothing noticed.

These tests are narrow on purpose. They assert the claims that went
stale, not the wording around them, so rewording Step 7 leaves them
green while removing a control or a story section turns them red.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tome.channels.canary import CANARY_TARGETS
from tome.models import RETRIEVAL_CHANNELS

SKILL = Path(__file__).parents[3] / "skills" / "research" / "SKILL.md"


@pytest.fixture(scope="module")
def skill_text() -> str:
    return SKILL.read_text(encoding="utf-8")


class TestTheSkillDoesNotUnderclaimTheControls:
    """Scenario: Controls exist, so the prose must not say they do not."""

    def test_it_does_not_claim_controls_are_unimplemented(
        self, skill_text: str
    ) -> None:
        """
        Given canary targets are defined for every retrieval channel
        Then SKILL.md does not tell the operator none are emitted

            This is the exact sentence that went stale. An operator who
            believes INCONCLUSIVE is a placeholder will scroll past a
            blind channel, which is the one message the verdict exists
            to deliver.
        """
        assert CANARY_TARGETS, "precondition: targets are defined"
        stale = [
            "no channel emits a positive control yet",
            "until canary targets exist",
        ]
        for claim in stale:
            assert claim not in skill_text.lower(), (
                f"SKILL.md still claims {claim!r}, but "
                f"{sorted(CANARY_TARGETS)} have canary targets"
            )

    def test_it_tells_the_operator_which_channels_are_controlled(
        self, skill_text: str
    ) -> None:
        """
        Given the verdict rests on retrieval channels only
        Then SKILL.md says triz is excluded from it

            An operator who thinks triz votes will read a verdict that
            ignored it as a bug, or worse, will trust a coverage claim
            they believe includes generated analogies.
        """
        assert "triz" in skill_text
        assert "excluded from the verdict" in skill_text.lower()
        assert "triz" not in RETRIEVAL_CHANNELS, "precondition"


class TestTheSkillRoutesStoriesToAHuman:
    """Scenario: Stories are presented for triage, not auto-filed."""

    def test_it_instructs_presenting_the_stories(self, skill_text: str) -> None:
        """
        Given the report now carries a Research Stories section
        Then SKILL.md tells the operator to surface it
        """
        assert "frontier_stories" in skill_text

    @pytest.mark.parametrize("disposition", ["act", "defer", "decline"])
    def test_it_offers_every_disposition(
        self, skill_text: str, disposition: str
    ) -> None:
        """
        Given a story arrives undecided
        Then SKILL.md names all three answers the operator may give

            Listing two of three quietly removes an option. "Not worth
            it" is the one most likely to be dropped and the one that
            keeps a backlog honest.
        """
        assert f"`{disposition}`" in skill_text

    def test_it_forbids_filing_an_issue_the_user_did_not_approve(
        self, skill_text: str
    ) -> None:
        """
        Given the tool proposes and a person disposes
        Then SKILL.md forbids filing a story nobody has marked

            An agent that files its own research directions as issues
            has decided what is worth the project's time, which is the
            judgment the whole design refuses to make.
        """
        text = skill_text.lower()
        assert "do not decide for them" in text
        assert "have not marked" in text

    def test_each_disposition_routes_somewhere_different(self, skill_text: str) -> None:
        """
        Given three dispositions with three different consequences
        Then defer is the one that files an issue

            The first draft of this instruction told the operator both
            to file nothing unmarked-act and to file on defer, which
            are incompatible. The guard above passed on both sides of
            that contradiction because it matches substrings rather
            than policy. This one pins the routing: a story only
            becomes an issue when someone chose to come back to it.
        """
        text = skill_text.lower()
        defer_clause = text[text.index("on `defer`") :][:200]
        assert "minister:create-issue" in defer_clause, (
            "defer must be the disposition that files an issue"
        )
        assert "not marked `act`" not in text, (
            "filing is gated on defer, so act must not also gate it"
        )
