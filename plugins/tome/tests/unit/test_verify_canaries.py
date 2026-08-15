"""A failing control means nothing until you know which thing failed.

Feature: Canary targets are re-verified, and outcomes are distinguished.

As someone maintaining the retrieval channels
I want a failed control classified rather than merely reported
So that I investigate the channel only when the channel is the problem

The three canary targets are third-party documents. A target that moved
and a channel that broke produce the same observation from inside the
verdict: the control did not come back. They call for opposite actions,
though. A moved target means edit ``canary.py``. A broken channel means
every recent session using it is suspect.

So the job classifies four ways, and only two of them are defects:

``RETRIEVED``       the expected document came back
``TARGET_MOVED``    the channel answered fine, the document was not there
``CHANNEL_ERROR``   transport failure, 5xx, or an unparseable body
``RATE_LIMITED``    429, which is not a verdict about anything

The classifier is pure and takes an already-fetched response, so these
tests run offline. Fetching lives in a thin shell around it, which is
the same functional-core split the rest of tome uses.
"""

from __future__ import annotations

import pytest

from tome.models import RETRIEVAL_CHANNELS
from tome.scripts.verify_canaries import (
    CHANNEL_ERROR,
    RATE_LIMITED,
    RETRIEVED,
    TARGET_MOVED,
    _fetch,
    _https_only_opener,
    classify_canary_response,
    exit_code_for,
)

# Minimal bodies standing in for each service's real answer.
_HITS = {
    "academic": "<entry><title>Attention Is All You Need</title></entry>",
    "code": '{"total_count": 1, "items": [{"full_name": "torvalds/linux"}]}',
    "discourse": '{"hits": [{"title": "Y Combinator", "author": "pg"}]}',
}
_ANSWERED_BUT_EMPTY = {
    "academic": "<feed></feed>",
    "code": '{"total_count": 0, "items": []}',
    "discourse": '{"hits": []}',
}


class TestAPassingControl:
    """Scenario: The expected document came back."""

    @pytest.mark.parametrize("channel", sorted(RETRIEVAL_CHANNELS))
    def test_the_expected_document_passes(self, channel: str) -> None:
        """
        Given a 200 carrying the target document
        Then the outcome is RETRIEVED
        """
        outcome = classify_canary_response(channel, status=200, body=_HITS[channel])
        assert outcome.result == RETRIEVED


class TestTellingAMovedTargetFromABrokenChannel:
    """Scenario: The distinction the whole job exists to make."""

    @pytest.mark.parametrize("channel", sorted(RETRIEVAL_CHANNELS))
    def test_a_clean_answer_without_the_target_is_a_moved_target(
        self, channel: str
    ) -> None:
        """
        Given a 200 with a well-formed but empty result set
        Then the outcome is TARGET_MOVED, not CHANNEL_ERROR

            The service is up and answering. What changed is the
            document, so the fix is in canary.py and no channel needs
            investigating.
        """
        outcome = classify_canary_response(
            channel, status=200, body=_ANSWERED_BUT_EMPTY[channel]
        )
        assert outcome.result == TARGET_MOVED

    @pytest.mark.parametrize("channel", sorted(RETRIEVAL_CHANNELS))
    def test_a_server_error_is_a_channel_error(self, channel: str) -> None:
        """
        Given a 503
        Then the outcome is CHANNEL_ERROR
        """
        outcome = classify_canary_response(channel, status=503, body="")
        assert outcome.result == CHANNEL_ERROR

    @pytest.mark.parametrize("channel", sorted(RETRIEVAL_CHANNELS))
    def test_an_unparseable_body_is_a_channel_error(self, channel: str) -> None:
        """
        Given a 200 whose body cannot be parsed
        Then the outcome is CHANNEL_ERROR, not TARGET_MOVED

            Garbage is not evidence that a document moved. Reading it
            as TARGET_MOVED would send a maintainer to edit a URL that
            was fine.
        """
        outcome = classify_canary_response(
            channel, status=200, body="<<< not what this service returns >>>"
        )
        assert outcome.result == CHANNEL_ERROR


class TestRateLimitsAreNotVerdicts:
    """Scenario: 429 says try again, not that anything is broken."""

    @pytest.mark.parametrize("channel", sorted(RETRIEVAL_CHANNELS))
    def test_a_429_is_its_own_outcome(self, channel: str) -> None:
        """
        Given a 429
        Then the outcome is RATE_LIMITED
        """
        outcome = classify_canary_response(channel, status=429, body="")
        assert outcome.result == RATE_LIMITED

    def test_a_rate_limit_does_not_fail_the_job(self) -> None:
        """
        Given a run where one channel was rate-limited and none broke
        Then the exit code is zero

            Semantic Scholar 429'd during the original target
            verification. A job that reddened on throttling would train
            its operator to rerun until green, which is how a real
            defect gets rerun away.
        """
        assert exit_code_for([RATE_LIMITED, RETRIEVED, RETRIEVED]) == 0


class TestTheExitCodeMatchesTheAction:
    """Scenario: Nonzero means someone has to do something."""

    @pytest.mark.parametrize("defect", [TARGET_MOVED, CHANNEL_ERROR])
    def test_a_defect_fails_the_job(self, defect: str) -> None:
        """
        Given any run containing a moved target or a broken channel
        Then the exit code is nonzero
        """
        assert exit_code_for([RETRIEVED, defect, RETRIEVED]) != 0

    def test_an_all_clear_run_succeeds(self) -> None:
        """Scenario: Three passes, nothing to do."""
        assert exit_code_for([RETRIEVED, RETRIEVED, RETRIEVED]) == 0


class TestTheOutcomeCarriesItsRemedy:
    """Scenario: The operator is told what to do, not just what happened."""

    @pytest.mark.parametrize(
        "status,body_key,expected_word",
        [(200, "empty", "canary.py"), (503, "hit", "investigate")],
    )
    def test_each_outcome_names_its_next_action(
        self, status: int, body_key: str, expected_word: str
    ) -> None:
        """
        Given a failing outcome
        Then its remedy names the file to edit or the thing to check

            A classification the reader has to interpret is a
            classification that gets interpreted wrong at 2am.
        """
        body = _ANSWERED_BUT_EMPTY["code"] if body_key == "empty" else _HITS["code"]
        outcome = classify_canary_response("code", status=status, body=body)
        assert expected_word in outcome.remedy.lower()


class TestTheFetcherCanOnlySpeakHttps:
    """Scenario: A control cannot be satisfied without leaving the machine.

    ``urlopen`` handles ``file:``, ``ftp:`` and ``data:`` as well as
    http. A canary target edited to a local path would then read as a
    passing control while touching no network at all, which is worse
    than having no control, because it looks like evidence.

    The obvious fix is a trap. ``build_opener(HTTPSHandler())`` keeps
    the default ``FileHandler``, so it still reads local files while
    looking restrictive. Verified while writing this: it returned the
    contents of /etc/hostname. These tests pin the property rather than
    the construction, so swapping back to the trap turns them red.
    """

    def test_the_opener_carries_no_file_or_ftp_handler(self) -> None:
        """
        Given the module's opener
        Then it has no handler for any local or non-https scheme
        """
        installed = {type(h).__name__ for h in _https_only_opener().handlers}
        assert not installed & {"FileHandler", "FTPHandler", "DataHandler"}

    def test_the_opener_will_not_read_a_local_file(self) -> None:
        """
        Given a file:// URL
        Then the opener yields nothing rather than the file's contents

            The behavioural half. A handler roster can be satisfied by
            a subclass rename; actually declining to read the file
            cannot.
        """
        assert _https_only_opener().open("file:///etc/hostname") is None

    def test_a_non_https_target_is_refused_before_any_open(self) -> None:
        """
        Given a canary target that is not https
        Then _fetch raises rather than returning a fetch result

            The opener declining quietly would surface as an empty read
            and classify as CHANNEL_ERROR, sending a maintainer after a
            channel that is fine. Raising names the real problem.
        """
        with pytest.raises(ValueError, match="must be https"):
            _fetch("file:///etc/hostname")
