"""Challenge generation for the gauntlet plugin."""

from __future__ import annotations

import random
import uuid
from collections.abc import Callable

from gauntlet.models import (
    BankProblem,
    Challenge,
    ChallengeType,
    DeveloperProgress,
    KnowledgeEntry,
)
from gauntlet.problem_bank import bank_problem_to_challenge

# ---------------------------------------------------------------------------
# Generator type alias
# ---------------------------------------------------------------------------

_Generator = Callable[[KnowledgeEntry], Challenge]

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _make_id() -> str:
    return "ch-" + uuid.uuid4().hex[:12]


def _scope(entry: KnowledgeEntry) -> list[str]:
    """Deduplicated list of [module] + related_files."""
    seen: dict[str, None] = {}
    for item in [entry.module] + entry.related_files:
        seen[item] = None
    return list(seen)


# ---------------------------------------------------------------------------
# Individual generators
# ---------------------------------------------------------------------------


def _generate_multiple_choice(entry: KnowledgeEntry) -> Challenge:
    """Generate a multiple-choice challenge."""
    correct = entry.detail[:120].rstrip()

    distractors = [
        f"Not related to {entry.concept}",
        f"Applies only outside {entry.module}",
        "Deprecated behaviour removed in a later version",
    ]

    options = [correct] + distractors
    random.shuffle(options)
    letter = chr(ord("A") + options.index(correct))

    return Challenge(
        id=_make_id(),
        type=ChallengeType.MULTIPLE_CHOICE,
        knowledge_entry_id=entry.id,
        difficulty=entry.difficulty,
        prompt=(
            f"What best describes '{entry.concept}' in {entry.module}?\n\n"
            + "\n".join(f"{chr(ord('A') + i)}) {opt}" for i, opt in enumerate(options))
        ),
        context=entry.detail,
        answer=letter,
        options=options,
        hints=[f"Look at the module: {entry.module}"],
        scope_files=_scope(entry),
    )


def _generate_explain_why(entry: KnowledgeEntry) -> Challenge:
    """Generate an explain-why challenge."""
    return Challenge(
        id=_make_id(),
        type=ChallengeType.EXPLAIN_WHY,
        knowledge_entry_id=entry.id,
        difficulty=entry.difficulty,
        prompt=(
            f"Explain why '{entry.concept}' in {entry.module} works the way it does."
        ),
        context=entry.detail,
        answer=entry.detail,
        hints=[f"Consider the role of {entry.module}"],
        scope_files=_scope(entry),
    )


def _generate_trace(entry: KnowledgeEntry) -> Challenge:
    """Generate a data-flow trace challenge."""
    return Challenge(
        id=_make_id(),
        type=ChallengeType.TRACE,
        knowledge_entry_id=entry.id,
        difficulty=entry.difficulty,
        prompt=(
            f"Trace the data flow for '{entry.concept}' in {entry.module}. "
            "Describe what happens step by step."
        ),
        context=entry.detail,
        answer=entry.detail,
        hints=[f"Start from the entry point in {entry.module}"],
        scope_files=_scope(entry),
    )


def _generate_spot_bug(entry: KnowledgeEntry) -> Challenge:
    """Generate a spot-the-bug challenge."""
    return Challenge(
        id=_make_id(),
        type=ChallengeType.SPOT_BUG,
        knowledge_entry_id=entry.id,
        difficulty=entry.difficulty,
        prompt=(
            f"What could go wrong if the rule '{entry.concept}' in "
            f"{entry.module} is violated?"
        ),
        context=entry.detail,
        answer=entry.detail,
        hints=[f"Think about invariants maintained by {entry.module}"],
        scope_files=_scope(entry),
    )


def _generate_dependency_map(entry: KnowledgeEntry) -> Challenge:
    """Generate a dependency-map challenge."""
    answer = ", ".join(entry.related_files) if entry.related_files else entry.module
    return Challenge(
        id=_make_id(),
        type=ChallengeType.DEPENDENCY_MAP,
        knowledge_entry_id=entry.id,
        difficulty=entry.difficulty,
        prompt=(
            f"Which modules or files are affected by '{entry.concept}' "
            f"in {entry.module}? List them separated by commas."
        ),
        context=entry.detail,
        answer=answer,
        hints=[f"Consider what imports from {entry.module}"],
        scope_files=_scope(entry),
    )


def _generate_code_completion(entry: KnowledgeEntry) -> Challenge:
    """Generate a code-completion challenge."""
    return Challenge(
        id=_make_id(),
        type=ChallengeType.CODE_COMPLETION,
        knowledge_entry_id=entry.id,
        difficulty=entry.difficulty,
        prompt=(
            f"Complete the key logic that implements '{entry.concept}' "
            f"in {entry.module}. Describe or write the critical code."
        ),
        context=entry.detail,
        answer=entry.detail,
        hints=[f"The implementation lives in {entry.module}"],
        scope_files=_scope(entry),
    )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

CHALLENGE_TYPES: dict[str, _Generator] = {
    "multiple_choice": _generate_multiple_choice,
    "code_completion": _generate_code_completion,
    "trace": _generate_trace,
    "explain_why": _generate_explain_why,
    "spot_bug": _generate_spot_bug,
    "dependency_map": _generate_dependency_map,
}

_ALL_TYPES = list(CHALLENGE_TYPES.keys())

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def select_challenge_type(progress: DeveloperProgress) -> str:
    """Weighted random selection of challenge type.

    Unseen types get weight 3.0.
    Seen types get ``max(0.5, 2.0 - accuracy * 2.0)``.
    """
    weights: list[float] = []
    for ctype in _ALL_TYPES:
        records = [r for r in progress.history if r.challenge_type == ctype]
        if not records:
            weights.append(3.0)
        else:
            accuracy = sum(r.score() for r in records) / len(records)
            weights.append(max(0.5, 2.0 - accuracy * 2.0))

    return random.choices(_ALL_TYPES, weights=weights, k=1)[0]


def generate_challenge(entry: KnowledgeEntry, challenge_type: str) -> Challenge:
    """Delegate to the registered generator for *challenge_type*."""
    return CHALLENGE_TYPES[challenge_type](entry)


def generate_bank_challenge(problem: BankProblem) -> Challenge:
    """Generate a challenge from a standalone bank problem."""
    return bank_problem_to_challenge(problem)
