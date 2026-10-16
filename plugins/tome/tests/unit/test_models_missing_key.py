"""A missing key names the record it is missing from."""

from __future__ import annotations

import pytest

from tome.models import Finding, ResearchSession

_SESSION = {
    "id": "s1",
    "topic": "t",
    "domain": "d",
    "triz_depth": "light",
    "channels": ["code"],
}


@pytest.mark.unit
def test_missing_key_in_a_nested_finding_names_the_finding() -> None:
    session = {**_SESSION, "findings": [{"source": "x"}]}

    with pytest.raises(KeyError) as caught:
        ResearchSession.from_dict(session)

    message = str(caught.value)
    assert "Finding.from_dict missing required field" in message
    assert "ResearchSession.from_dict" not in message


@pytest.mark.unit
def test_missing_key_on_the_session_names_the_session() -> None:
    with pytest.raises(KeyError, match="ResearchSession.from_dict missing"):
        ResearchSession.from_dict({"id": "s1"})


@pytest.mark.unit
def test_missing_key_on_a_finding_names_the_finding() -> None:
    with pytest.raises(KeyError, match="Finding.from_dict missing"):
        Finding.from_dict({"source": "x"})
