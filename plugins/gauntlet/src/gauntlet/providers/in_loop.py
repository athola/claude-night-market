"""In-loop variation provider that avoids Anthropic SDK roundtrips.

When gauntlet runs inside Claude Code, calling out to the Anthropic
API to spawn a sibling Claude is wasteful: the parent LLM is already
in-loop. This module implements an alternative
``VariationProvider`` that produces deterministic local variations
by perturbing integers and small numeric tokens in the seed prompt,
plus a helper that detects the Claude Code runtime and registers
the provider in place of the default.

The provider is intentionally simple. Its job is to produce a prompt
that is meaningfully different from the seed (so the gauntlet
challenge does not feel like a memorisation drill) while making
zero outbound API calls. The skill itself can layer model-driven
rephrasing on top of the returned string when richer variations are
needed.

Acceptance criteria covered (issue #464):

- New module exposes ``in_loop_variation_provider``.
- Auto-registration helper switches providers when running inside
  Claude Code.
- The default Anthropic provider remains untouched outside Claude
  Code.
- The provider does not import or call ``anthropic``.
"""

from __future__ import annotations

import os
import re
from typing import TYPE_CHECKING

from gauntlet.challenges import (
    anthropic_variation_provider,
    get_variation_provider,
    set_variation_provider,
)

if TYPE_CHECKING:
    from gauntlet.models import BankProblem


# Order matters: replace longer integers first so we do not corrupt
# matches inside other matches.
_INT_RE = re.compile(r"\b\d+\b")


def _shift_int(match: re.Match[str]) -> str:
    """Shift an integer by a deterministic, bounded delta.

    Even-length numbers shift by +2; odd-length by +3. The regex
    matches non-negative integers and the delta is always positive,
    so the result is always >= 2.
    """
    raw = match.group(0)
    delta = 2 if len(raw) % 2 == 0 else 3
    return str(int(raw) + delta)


def in_loop_variation_provider(
    prompt_template: str,  # unused: kept for VariationProvider signature parity
    problem: BankProblem,
) -> str | None:
    """Return a deterministic local variation of the problem prompt.

    The variation perturbs integer tokens in the seed prompt by a
    small fixed delta. This produces a prompt that is byte-distinct
    from the seed without touching its semantic structure.

    Returns ``None`` when no integers are present, signalling
    graceful fallback to the seed problem at the call site.
    """
    seed = problem.prompt
    if not _INT_RE.search(seed):
        return None
    varied = _INT_RE.sub(_shift_int, seed)
    if varied.strip() == seed.strip():
        return None
    return varied


def is_running_in_claude_code() -> bool:
    """Return True if the runtime appears to be Claude Code.

    Claude Code sets ``CLAUDE_PLUGIN_ROOT`` for plugin scripts and
    ``CLAUDECODE`` for general harness context. Either is enough to
    decide the provider switch.
    """
    return any(os.environ.get(var) for var in ("CLAUDE_PLUGIN_ROOT", "CLAUDECODE"))


def register_in_loop_provider_if_inside_claude_code(*, force: bool = False) -> bool:
    """Switch the active provider to in-loop when inside Claude Code.

    By default the swap only happens when the current active provider
    is still the package default (``anthropic_variation_provider``);
    a caller that has explicitly registered a different provider is
    respected. Pass ``force=True`` to swap unconditionally.

    Returns True iff the swap happened. Outside Claude Code the
    default Anthropic provider is left in place.
    """
    if not is_running_in_claude_code():
        return False
    if not force and get_variation_provider() is not anthropic_variation_provider:
        # A test or skill registered a custom provider on purpose;
        # leave it alone.
        return False
    set_variation_provider(in_loop_variation_provider)
    return True
