"""The interactive prompt shows what the recommender produced."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from architecture_researcher import ArchitectureResearcher, ProjectContext
from attune_arch_init import present_recommendation


@pytest.mark.unit
def test_alternatives_are_shown_with_their_rationale(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A recommendation with runners-up is presented, not a KeyError.

    recommend() writes each alternative's reason under "rationale", and
    the prompt read alt["reason"], so any interactive run with more than
    one candidate crashed before asking the question.
    """
    recommendation = ArchitectureResearcher(
        ProjectContext(
            project_type="web-api", domain_complexity="moderate", team_size="5-15"
        )
    ).recommend()
    assert recommendation.alternatives

    with patch("builtins.input", return_value="y"):
        assert present_recommendation(recommendation) is True

    shown = recommendation.alternatives[0]
    assert shown["rationale"] in capsys.readouterr().out
