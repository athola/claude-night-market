"""A payload WebFetch could not convert is not a knowledge capture.

Issue #661, defect 2. When WebFetch returns 2xx but cannot decode the
body (linearized or encoded PDFs are the usual case), the model writes
a short refusal narrative and that narrative is stored as research. Two
such captures landed in one session, one of them titled "Analysis:
Radio Equipment Specifications", which reads like real work in the
index. Their ``content_length`` was 1339 and 1199 against source
documents of 455 KB and 249 KB.

The existing guards do not reach this case: ``detect_failed_fetch_
status`` covers non-2xx transport failures (#547) and
``detect_null_capture`` covers redirect notices and empty result sets
(#649). Here the fetch is 2xx and the body is non-empty.

The obvious fix is the wrong one. ``detect_null_capture`` records that
two prose heuristics were tried against the live corpus and both
deleted real research, which is why nothing in this module reads the
summary text. Matching "I cannot extract" would repeat that mistake.

So this guard reads only what the tool itself emits: the binary-content
marker, the MIME type it names, and the size it reports against the
length of the extracted text. No sentence in the body is interpreted.

Feature: an unconverted binary payload is dropped, and a converted one
is kept.
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../hooks"))

from web_research_handler import detect_unconverted_binary

# The literal WebFetch appends when it saves a payload it could not
# convert. Anchoring on it keeps this as structural as the
# REDIRECT DETECTED marker the sibling guard uses.
MARKER = "[Binary content (application/pdf, 455.2KB) also saved to /tmp/webfetch-x.pdf]"

REFUSAL = (
    "I cannot extract the requested technical specifications from this "
    "document. The content appears to be a linearized PDF whose text "
    "layer is not accessible through this interface.\n\n" + MARKER
)


class TestUnconvertedBinaryIsRejected:
    """The two captures from the issue, and the shape they share."""

    def test_refusal_alongside_a_binary_marker_is_rejected(self) -> None:
        """GIVEN a 2xx response whose body is short and whose tool result
        carries the binary-content marker for a 455 KB source
        WHEN the guard runs
        THEN it returns a reason, so the caller drops the capture.
        """
        assert detect_unconverted_binary({}, REFUSAL) is not None

    def test_reason_names_the_condition(self) -> None:
        """GIVEN the same response
        WHEN the guard runs
        THEN the reason is machine-readable, matching how the sibling
        guards report ``redirect-notice`` and ``empty-results``.
        """
        assert detect_unconverted_binary({}, REFUSAL) == "unconverted-binary"

    def test_mime_type_on_the_response_is_honored(self) -> None:
        """GIVEN the marker is absent but the response declares a binary
        MIME type and the extracted text is a sliver of the content length
        WHEN the guard runs
        THEN it still rejects, since the same structural facts are present.
        """
        response = {"content_type": "application/pdf", "content_length": 455_000}

        assert detect_unconverted_binary(response, "I cannot extract this.") is not None


class TestRealExtractionSurvives:
    """The constraint that killed the two prose heuristics."""

    def test_substantial_text_from_a_binary_source_is_kept(self) -> None:
        """GIVEN a PDF that converted, so the marker is present but the
        extracted text is a real fraction of the source
        WHEN the guard runs
        THEN it returns None.

        This is the case a size-blind marker check would destroy: a
        converted PDF still reports that its bytes were saved.
        """
        extracted = "Section 1. " + ("substantive technical prose. " * 4000)
        assert detect_unconverted_binary({}, extracted + "\n" + MARKER) is None

    def test_short_page_without_a_binary_marker_is_kept(self) -> None:
        """GIVEN an ordinary short HTML page
        WHEN the guard runs
        THEN it returns None, because no structural signal fired.

        Brevity alone is not evidence: a real capture can be short.
        """
        assert detect_unconverted_binary({}, "A brief but real finding.") is None

    def test_prose_resembling_a_refusal_is_kept_without_a_marker(self) -> None:
        """GIVEN a genuine capture that happens to discuss extraction
        failure, with no binary marker and no binary MIME type
        WHEN the guard runs
        THEN it returns None.

        The guard must not read the sentence. An article about why PDF
        text layers fail is real research and says the same words.
        """
        content = (
            "The report explains why I cannot extract text from linearized "
            "PDFs without a rasterization pass, and benchmarks four tools "
            "against a 455KB corpus."
        )
        assert detect_unconverted_binary({}, content) is None


class TestDegradedInputs:
    """The guard runs on untrusted tool output and must not raise."""

    @pytest.mark.parametrize(
        "response",
        [{}, {"content_type": None}, {"content_length": "not-a-number"}, "a string"],
    )
    def test_malformed_response_does_not_raise(self, response: object) -> None:
        """GIVEN a response of an unexpected shape
        WHEN the guard runs
        THEN it returns a value rather than breaking the capture path.
        """
        assert detect_unconverted_binary(response, "some content") in (
            None,
            "unconverted-binary",
        )

    def test_empty_content_is_left_to_the_sibling_guard(self) -> None:
        """GIVEN an empty body and no marker
        WHEN the guard runs
        THEN it returns None: emptiness is ``detect_null_capture``'s
        concern, and two guards claiming one condition is how a fix
        starts contradicting itself.
        """
        assert detect_unconverted_binary({}, "") is None
