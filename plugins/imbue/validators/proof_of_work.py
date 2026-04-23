#!/usr/bin/env python3
"""Nen Court validator: Proof-of-work evidence audit (issue #406).

Graduates "Proof-of-work evidence" from Soft Vow to Nen Court.  Audits
agent output for the proof-of-work contract:

    - At least N evidence references in [E1] [E2] ... format
    - No unsupported claim phrases ("should work", "looks correct",
      "I think", "probably works") unless paired with an evidence ref
    - An explicit Status: PASS / FAIL / BLOCKED line

Verdict rules:

    pass         -- meets evidence threshold, status present, no
                    unsupported claims
    violation    -- below evidence threshold OR unsupported claim found
    inconclusive -- status line missing (cannot tell what happened)

Contract:

    input  (stdin JSON):
      {"text": "...", "min_evidence": N}

    output (stdout JSON):
      {
        "verdict": "pass" | "violation" | "inconclusive",
        "evidence": [{"kind": "...", "detail": "..."}, ...],
        "recommendation": "..."
      }

    exit code: 0=pass, 1=violation, 2=inconclusive
"""

from __future__ import annotations

import json
import re
import sys
from typing import Any

# Match [E1], [E2], ..., [E99] (one or two digits).  Anchored to
# [E followed by digits to avoid false positives like [Edge case].
_EVIDENCE_REF_PATTERN = re.compile(r"\[E(\d{1,2})\]")

# Phrases that signal a claim without proof.  Each is a regex with
# word boundaries.
_UNSUPPORTED_CLAIM_PHRASES = (
    r"\bshould work\b",
    r"\blooks? correct\b",
    r"\blooks? good\b",
    r"\bprobably works?\b",
    r"\bI think\b",
    r"\bseems? (?:to|like) (?:work|fine|right)\b",
)
_UNSUPPORTED_CLAIM_PATTERN = re.compile(
    "|".join(_UNSUPPORTED_CLAIM_PHRASES), re.IGNORECASE
)

_STATUS_PATTERN = re.compile(r"Status\s*[:=]\s*(PASS|FAIL|BLOCKED)", re.IGNORECASE)


def find_evidence_refs(text: str) -> set[str]:
    """Return the set of evidence ref tokens (e.g. {'E1', 'E2'}) found in *text*."""
    return {f"E{m.group(1)}" for m in _EVIDENCE_REF_PATTERN.finditer(text)}


def _sentences(text: str) -> list[str]:
    """Split *text* into sentences on .!? followed by whitespace.

    Naive splitter -- adequate for prose audit since false-positive
    over-segmentation only widens the safety net.
    """
    return [s for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def find_unsupported_claims(text: str) -> list[str]:
    """Return the matched substrings of unsupported claim phrases.

    A claim paired with an evidence ref ([E1]..[En]) in the SAME
    sentence is considered supported and not flagged.  Evidence in a
    neighbouring sentence does NOT count -- the [Ex] must directly
    accompany the claim.
    """
    flagged: list[str] = []
    for sentence in _sentences(text):
        if _EVIDENCE_REF_PATTERN.search(sentence):
            continue
        for m in _UNSUPPORTED_CLAIM_PATTERN.finditer(sentence):
            flagged.append(m.group(0))
    return flagged


def extract_status(text: str) -> str | None:
    """Return the status token in lowercase ('pass', 'fail', 'blocked') or None."""
    m = _STATUS_PATTERN.search(text)
    if m is None:
        return None
    return m.group(1).lower()


def validate_output(text: str, *, min_evidence: int = 3) -> dict[str, Any]:
    """Validate an agent output document.

    Returns a verdict dict.  See module docstring for verdict rules.
    """
    refs = find_evidence_refs(text)
    claims = find_unsupported_claims(text)
    status = extract_status(text)

    evidence: list[dict[str, Any]] = []

    if claims:
        for c in claims:
            evidence.append(
                {
                    "kind": "unsupported_claim",
                    "detail": (
                        f'unsupported claim: "{c}" appears without an '
                        "[Ex] evidence reference in the same paragraph"
                    ),
                }
            )

    if len(refs) < min_evidence:
        evidence.append(
            {
                "kind": "insufficient_evidence",
                "detail": (
                    f"found {len(refs)} evidence refs, need at least "
                    f"{min_evidence}.  Add [E1], [E2], ... citations "
                    "for tested claims."
                ),
            }
        )

    if status is None:
        # Status line missing but otherwise compliant -> inconclusive.
        if not claims and len(refs) >= min_evidence:
            return {
                "verdict": "inconclusive",
                "evidence": [
                    {
                        "kind": "missing_status",
                        "detail": (
                            "no Status: PASS|FAIL|BLOCKED line found; "
                            "cannot determine reported outcome"
                        ),
                    }
                ],
                "recommendation": (
                    "Add a 'Status: PASS|FAIL|BLOCKED' line at the end of the output."
                ),
            }
        # If there are also other problems, they take precedence.
        evidence.append(
            {
                "kind": "missing_status",
                "detail": "no Status: line found",
            }
        )

    if evidence:
        return {
            "verdict": "violation",
            "evidence": evidence,
            "recommendation": (
                "Proof-of-work: cite tested claims with [E1], [E2], ... "
                "references and end with an explicit Status line.  "
                "'should work' and 'looks correct' are red flags -- "
                "run the test, capture output, and cite it."
            ),
        }

    return {"verdict": "pass", "evidence": [], "recommendation": ""}


def main() -> None:
    """Entry point for stdin-driven validator invocation."""
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError as exc:
        print(
            json.dumps(
                {
                    "verdict": "inconclusive",
                    "evidence": [{"error": f"invalid JSON on stdin: {exc}"}],
                    "recommendation": "Send a JSON object with 'text'.",
                }
            )
        )
        sys.exit(2)

    text = payload.get("text")
    if text is None:
        print(
            json.dumps(
                {
                    "verdict": "inconclusive",
                    "evidence": [{"error": "missing 'text' key"}],
                    "recommendation": "Send a JSON object with 'text'.",
                }
            )
        )
        sys.exit(2)

    min_evidence = int(payload.get("min_evidence", 3))
    result = validate_output(str(text), min_evidence=min_evidence)
    print(json.dumps(result))
    if result["verdict"] == "pass":
        sys.exit(0)
    if result["verdict"] == "violation":
        sys.exit(1)
    sys.exit(2)


if __name__ == "__main__":
    main()
