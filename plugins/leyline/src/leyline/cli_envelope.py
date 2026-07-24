"""Standard envelope shape for CLI scripts that emit JSON results.

Plugin scripts (test_generator, quality_checker, safe_replacer)
wrap their results in ``{"success": bool, ...}`` envelopes so
downstream tooling can detect success without parsing prose.
This module exposes that contract so future scripts cannot drift
on key names, ordering, or shape (D-13).

The structural shape is also exported as ``SuccessEnvelope`` /
``ErrorEnvelope`` ``TypedDict``s plus a discriminated ``Envelope``
union (S9, issue #484). Static type checkers can narrow on the
``success`` literal at the call site.
"""

from typing import TYPE_CHECKING, Any, Literal, TypedDict


class SuccessEnvelope(TypedDict):
    """Wire shape returned by :func:`success_envelope`.

    The ``success`` field is the discriminator for the
    :data:`Envelope` union; consumers narrow on it before reading
    ``data`` vs ``error``.
    """

    success: Literal[True]
    data: Any


class ErrorEnvelope(TypedDict):
    """Wire shape returned by :func:`error_envelope`."""

    success: Literal[False]
    error: str


# Discriminated union: narrowing on env["success"] picks a branch.
if TYPE_CHECKING:
    # Type checkers see the real union (``X | Y`` is what ruff's UP007
    # wants, and this branch never runs).
    Envelope = SuccessEnvelope | ErrorEnvelope
else:
    # ``Envelope`` is exported in ``__all__`` and imported by consumers, so
    # the name must exist at runtime. A concrete placeholder provides it
    # while avoiding ``|`` on ``TypedDict`` classes, which is 3.10+ and
    # would break the Python 3.9 floor at import time.
    Envelope = dict


def success_envelope(data: Any) -> SuccessEnvelope:
    """Wrap a successful CLI result for JSON emission.

    Returns ``{"success": True, "data": data}``.

    Note: ``data`` must be JSON-serializable by the caller.
    Callers that may pass non-serializable values (Path, datetime,
    custom objects) should pass ``default=str`` to
    ``json.dumps``. F4 from /pensive:full-review documented this
    contract after observing a TypeError leak from
    ``safe_replacer`` and ``test_generator``.
    """
    return {"success": True, "data": data}


def error_envelope(message: str) -> ErrorEnvelope:
    """Wrap a CLI error message for JSON emission.

    Returns ``{"success": False, "error": message}``.
    """
    return {"success": False, "error": message}


__all__ = [
    "Envelope",
    "ErrorEnvelope",
    "SuccessEnvelope",
    "error_envelope",
    "success_envelope",
]
