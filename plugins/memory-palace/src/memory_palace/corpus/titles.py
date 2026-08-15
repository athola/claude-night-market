"""Shape rules for what counts as a captured page title.

A title names a thing; prose describes one. The capture hook has to
make that call on every fetch, and the index promoter has to make the
same call when repairing titles the hook stored before these rules
were right. Both need one answer, so the rules live here rather than
in the hook that happens to have needed them first.

The rules are shape checks, not a phrase blocklist. Model phrasing
drifts and a phrase list rots; the shape of a bullet does not. Where a
literal list survives (``_PREAMBLE_OPENERS``, ``_GENERIC_HEADINGS``)
it is kept deliberately short and, for the generics, matched
whole-line, so a real title that merely contains the word is untouched.

History: #621 added the length, terminal-punctuation and opener checks
after model preamble reached the promotion tier. #624 added the
list-marker and generic-heading checks after answer-body fragments did
the same. The emphasis strip was added after refusal sentences
reached the index wearing bold markers that hid both their terminal
colon and their opener.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

TITLE_MAX_CHARS = 100

# Openers that mark a line as the model talking about the page rather
# than the page's own title. Kept deliberately short: the shape checks
# do most of the work, and a long phrase list would rot as model
# phrasing drifts (#621).
_PREAMBLE_OPENERS = (
    "based on",
    "here is",
    "here's",
    "here are",
    "i cannot",
    "i could not",
    "i couldn't",
    "i was unable",
    "unfortunately",
    "sorry",
    "redirect detected",
    "there are no",
    "no results",
)

# A bullet or ordered marker followed by whitespace. The trailing \s is
# load-bearing: it separates the bullet "* args" from the real title
# "*args and **kwargs in Python" (#624).
_LIST_MARKER = re.compile(r"^(?:[-*+]|\d+[.)])\s")

# Scaffolding headings the model emits when it has no page title to
# report. Matched whole-line rather than by prefix, so "Response Times
# Explained" survives while a bare "Response" does not (#624).
_GENERIC_HEADINGS = frozenset(
    {"response", "summary", "answer", "analysis", "overview", "results"}
)

# Emphasis markers, longest first so ``**`` is tried before ``*``.
# Only matched pairs are stripped, which is what keeps the unpaired
# marker in "*args and **kwargs in Python" from being eaten (#624).
_EMPHASIS_MARKERS = ("**", "__", "*", "_")


def _strip_emphasis(line: str) -> str:
    """Return the line with paired emphasis wrappers removed.

    A wrapper defeats two of the shape rules at once: it moves terminal
    punctuation inside the markers so the ``:`` check reads ``*``, and
    it pushes a preamble opener off the start of the string. That is
    how "**What I cannot provide based on this content:**" was stored
    as a page title and promoted to importance 80, while the same
    sentence without the wrapper was correctly rejected. Same hole as
    #649, reached through the title field rather than the score.

    Stripping happens on the evaluated copy only. The stored title is
    never rewritten here, so a genuinely emphasized real title is
    judged on its text and kept as captured.
    """
    stripped = line.strip()
    changed = True
    while changed:
        changed = False
        for marker in _EMPHASIS_MARKERS:
            width = len(marker)
            if (
                len(stripped) > 2 * width
                and stripped.startswith(marker)
                and stripped.endswith(marker)
            ):
                stripped = stripped[width:-width].strip()
                changed = True
                break
    return stripped


def looks_like_title(line: str) -> bool:
    """Report whether a line names a thing rather than describing it.

    Paired emphasis wrappers are stripped from the evaluated copy
    first, because a wrapper otherwise defeats checks 2 and 5 at once.
    Then five shape checks, ordered by how much junk each removes from
    the live index:

    1. Length. A line past ``TITLE_MAX_CHARS`` is a paragraph.
       Accepting it meant slicing mid-sentence, which is what stored
       "To get accurate answers to your questions about ServiceTitan's
       developer" as a page title.
    2. Terminal punctuation. Titles do not end in ``.``, ``:`` or
       ``,``. This alone rejects most model preambles. ``?`` and ``!``
       are allowed, because "What Is Rust Ownership?" is a real title.
    3. List markers. A list item is a fragment of an answer body, and
       it clears checks 1, 2 and 5 easily: it is short, it ends on a
       word, and it opens with a bullet rather than a known phrase.
       This is what stored "- A loading state".
    4. Generic scaffolding headings, whole-line only.
    5. Preamble openers, as a narrow backstop for preambles that carry
       no terminal punctuation.
    """
    line = _strip_emphasis(line)
    if not line:
        return False
    if len(line) > TITLE_MAX_CHARS:
        return False
    if line.endswith((".", ":", ",", ";")):
        return False
    if _LIST_MARKER.match(line):
        return False
    lowered = line.casefold()
    if lowered in _GENERIC_HEADINGS:
        return False
    return not lowered.startswith(_PREAMBLE_OPENERS)


def slug_title_from_url(url: str) -> str | None:
    """Derive a title from the URL's last path segment, or None.

    Returns None when the URL carries no path to read, which is the
    signal that there is nothing better than what the caller already
    has. A bare hostname is not an improvement over a bad title, and
    rewriting the index to gain nothing is its own defect (#605).
    """
    if not url:
        return None
    path_parts = [p for p in urlparse(url).path.split("/") if p]
    if not path_parts:
        return None
    words = path_parts[-1].replace("-", " ").replace("_", " ").split()
    if not words:
        return None
    return " ".join(words).title()[:TITLE_MAX_CHARS].strip() or None


def title_from_url(url: str) -> str:
    """Derive a display title from a URL, falling back to the host.

    The capture hook always needs *some* title, so unlike
    :func:`slug_title_from_url` this never returns None.
    """
    return slug_title_from_url(url) or urlparse(url).netloc
