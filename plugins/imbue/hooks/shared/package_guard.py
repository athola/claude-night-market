"""Package-hallucination guard logic (shared, network-free core).

Code-generating LLMs recommend packages that do not exist at a
measured rate of 5.2% (commercial models) to 21.7% (open models)
across 576,000 samples (Spracklen et al. 2024, arXiv 2406.10279), and
58% of hallucinated names recur across reruns, making them stable
slopsquatting targets. This module gives the imbue verification spine
a deterministic, offline-first defense:

1. ``parse_packages`` extracts the package names an install command
   would fetch, stripping versions, flags, local paths, and VCS URLs.
2. ``nearest_known`` flags names within a small edit distance of a
   popular package (the typosquat / slopsquat signal), using only a
   bundled known-popular set, so it needs no network.
3. ``assess_packages`` classifies each package and, only for names not
   in the known-popular set, consults an *injected* registry function.
   The registry call is injected (not imported) so the logic is fully
   testable without touching PyPI, npm, or crates.io.

The registry lookup itself (network) lives in the hook wrapper, which
passes it in. When the registry cannot be reached, the package is
reported as ``unverified`` rather than ``nonexistent`` -- the guard
never blocks on a network failure.
"""

from __future__ import annotations

import re
import time
from collections.abc import Callable

__all__ = [
    "KNOWN_POPULAR",
    "assess_packages",
    "levenshtein",
    "nearest_known",
    "normalize_name",
    "parse_packages",
]

# Ecosystem install-command signatures. Each entry maps a regex that
# matches the command head to the ecosystem label used downstream.
_INSTALL_HEADS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^\s*(?:python[0-9.]*\s+-m\s+)?pip[0-9]*\s+install\b"), "pypi"),
    (re.compile(r"^\s*uv\s+pip\s+install\b"), "pypi"),
    (re.compile(r"^\s*uv\s+add\b"), "pypi"),
    (re.compile(r"^\s*(?:poetry|pdm)\s+add\b"), "pypi"),
    (re.compile(r"^\s*(?:npm|pnpm)\s+(?:install|i|add)\b"), "npm"),
    (re.compile(r"^\s*yarn\s+add\b"), "npm"),
    (re.compile(r"^\s*cargo\s+add\b"), "crates"),
]

# Tokens that are flags, not package names.
_FLAG_RE = re.compile(r"^-")
# Flags that consume the following token as their value (a file or path,
# never a registry package name): -r req.txt, -c constraints.txt, -e path.
_VALUE_FLAGS = frozenset(
    {"-r", "--requirement", "-c", "--constraint", "-e", "--editable"}
)
# Where one shell command ends and the next begins. A subshell or command
# substitution opener and closer also start a new command, so the install
# inside "(pip install x)" or "$(pip install x)" heads its own segment.
_SHELL_SEPARATOR_RE = re.compile(r"&&|\|\||\$\(|[;|&\n()`]")
# A descriptor duplication ("2>&1", ">&2") holds an "&" that is not a
# separator; it is removed before the command is split.
_FD_DUP_RE = re.compile(r"\d*[<>]&\d*-?")
# A redirection operator; bare, its target is the next token.
_REDIRECT_RE = re.compile(r"^\d*(?:>>?|<)")
# Words that run the command after them: "sudo pip install x" fetches x.
# Their flags and "NAME=value" assignments are skipped with them, and
# the user, group and directory flags of sudo and env take a value.
_COMMAND_PREFIX_RE = re.compile(
    r"^\s*(?:(?:sudo|env|nohup|time|command|exec)\s+(?:-[ugC]\s+\S+\s+|-\S+\s+)*"
    r"|[A-Za-z_][A-Za-z0-9_]*=\S*\s+)+"
)
# Targets that are local paths or VCS/URL references, never a registry name.
_NON_REGISTRY_RE = re.compile(
    r"(^[./~])|(^[a-z]+\+)|(://)|(\.git$)|(^\.$)|(^[^@].*/)|(\.(whl|zip|tar\.gz|tgz)$)"
)

# Curated known-popular packages per ecosystem. Two jobs:
#   - common installs short-circuit before any network call;
#   - they are the reference set for typosquat distance.
# Intentionally modest: the top, most-impersonated names. Extend freely.
KNOWN_POPULAR: dict[str, frozenset[str]] = {
    "pypi": frozenset(
        {
            "requests",
            "numpy",
            "pandas",
            "flask",
            "django",
            "fastapi",
            "pydantic",
            "httpx",
            "aiohttp",
            "pytest",
            "scipy",
            "scapy",
            "scikit-learn",
            "matplotlib",
            "pillow",
            "boto3",
            "sqlalchemy",
            "click",
            "rich",
            "tqdm",
            "pyyaml",
            "setuptools",
            "wheel",
            "torch",
            "tensorflow",
            "transformers",
            "openai",
            "anthropic",
            "beautifulsoup4",
            "lxml",
            "urllib3",
            "certifi",
            "cryptography",
            "redis",
            "celery",
            "uvicorn",
            "starlette",
            "jinja2",
            "werkzeug",
            "ruff",
            "mypy",
            "black",
        }
    ),
    "npm": frozenset(
        {
            "react",
            "react-dom",
            "vue",
            "angular",
            "express",
            "lodash",
            "axios",
            "typescript",
            "vite",
            "webpack",
            "eslint",
            "prettier",
            "jest",
            "vitest",
            "next",
            "tailwindcss",
            "zod",
            "chalk",
            "commander",
            "left-pad",
            "dotenv",
            "moment",
            "uuid",
            "rxjs",
            "redux",
            "svelte",
        }
    ),
    "crates": frozenset(
        {
            "serde",
            "tokio",
            "clap",
            "rand",
            "regex",
            "reqwest",
            "anyhow",
            "thiserror",
            "syn",
            "quote",
            "log",
            "tracing",
            "futures",
            "hyper",
            "serde_json",
            "itertools",
            "chrono",
            "rayon",
            "bytes",
            "async-trait",
        }
    ),
}

# Names within this edit distance of a known-popular package, but not
# themselves known, are treated as typosquat / slopsquat suspects.
_TYPOSQUAT_MAX_DISTANCE = 2


# Below these lengths a name gets no typo distance, then one edit.
_SHORT_NAME = 5
_MEDIUM_NAME = 8


def _allowed_distance(name: str) -> int:
    """Edits a name of this length may be from a popular one and still be a typo.

    Short names crowd together: ``sync`` is one edit from ``syn`` and
    ``numba`` two from ``numpy``, both real. A flat distance of 2 blocked
    them in enforce mode. Under five characters nothing is judged, under
    eight one edit is, and longer names get the full two.
    """
    if len(name) < _SHORT_NAME:
        return 0
    if len(name) < _MEDIUM_NAME:
        return 1
    return _TYPOSQUAT_MAX_DISTANCE


def _typo_distance(a: str, b: str) -> int:
    """Levenshtein distance with an adjacent swap counted as one edit.

    A swapped pair (``nmupy``) is the commonest typo and the commonest
    squat, and plain Levenshtein charges it two.
    """
    rows = [list(range(len(b) + 1))]
    for i in range(1, len(a) + 1):
        row = [i] + [0] * len(b)
        for j in range(1, len(b) + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            row[j] = min(rows[i - 1][j] + 1, row[j - 1] + 1, rows[i - 1][j - 1] + cost)
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                row[j] = min(row[j], rows[i - 2][j - 2] + 1)
        rows.append(row)
    return rows[-1][-1]


def parse_packages(command: str) -> list[tuple[str, str]]:
    """Return ``(ecosystem, name)`` pairs an install command would fetch.

    Versions (``==``, ``@``, ``>=``...), flags, local paths, and VCS
    URLs are stripped. A non-install command returns an empty list.
    """
    # Each command in a chain ("a && b; c | d") runs, so each is parsed on
    # its own. "pip install x && pytest" reads only x; "pip install x &&
    # pip install y" reads both.
    packages: list[tuple[str, str]] = []
    for segment in _SHELL_SEPARATOR_RE.split(_FD_DUP_RE.sub(" ", command)):
        text = _COMMAND_PREFIX_RE.sub("", segment).strip()
        packages.extend(_parse_install_segment(text))
    return packages


def _parse_install_segment(text: str) -> list[tuple[str, str]]:
    """Parse one separator-free command; a non-install returns ``[]``."""
    ecosystem = None
    head = None
    for pattern, eco in _INSTALL_HEADS:
        match = pattern.match(text)
        if match:
            ecosystem = eco
            head = match.group(0)
            break
    if ecosystem is None or head is None:
        return []

    packages: list[tuple[str, str]] = []
    skip_next = False
    for token in text[len(head) :].split():
        if skip_next:
            skip_next = False
            continue
        if token.startswith("#"):
            break  # the rest of the line is a comment
        redirect = _REDIRECT_RE.match(token)
        if redirect:
            # Bare ("> log") names its file in the next token.
            skip_next = redirect.end() == len(token)
            continue
        if token in _VALUE_FLAGS:
            skip_next = True
            continue
        if _FLAG_RE.match(token):
            continue
        unquoted = token.strip("'\"")
        if _NON_REGISTRY_RE.search(unquoted):
            continue
        name = _strip_version(unquoted)
        if name:
            packages.append((ecosystem, name))
    return packages


def _strip_version(token: str) -> str:
    """Strip a version specifier from a package token.

    Handles ``requests==2.31``, ``left-pad@1.3.0``, ``numpy>=1.20``, and
    bare ``serde``. A leading ``@scope/name`` npm token keeps its scope.
    """
    # Preserve npm scoped names: @scope/name (the @ is at position 0).
    if token.startswith("@") and "/" in token:
        scope, _, rest = token.partition("/")
        rest = re.split(r"[@<>=!~^]", rest, maxsplit=1)[0]
        return f"{scope}/{rest}"
    return re.split(r"[@<>=!~^\[]", token, maxsplit=1)[0]


def levenshtein(a: str, b: str) -> int:
    """Return the Levenshtein edit distance between two strings."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        current = [i]
        for j, cb in enumerate(b, start=1):
            cost = 0 if ca == cb else 1
            current.append(
                min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + cost)
            )
        previous = current
    return previous[-1]


_PEP503_SEPARATORS = re.compile(r"[-_.]+")


def normalize_name(name: str, ecosystem: str) -> str:
    """Return the name a registry compares, so equivalent spellings match.

    PyPI compares names after lowercasing and collapsing runs of ``-``,
    ``_`` and ``.`` to ``-`` (PEP 503): ``scikit_learn`` and
    ``Requests`` are ``scikit-learn`` and ``requests``. Other ecosystems
    are compared as written.
    """
    if ecosystem == "pypi":
        return _PEP503_SEPARATORS.sub("-", name).lower()
    return name


def nearest_known(name: str, ecosystem: str) -> str | None:
    """Return a popular package this name likely typosquats, else None.

    Returns None when *name* is itself a known-popular package or is too
    distant from every known one to be a plausible typo.
    """
    known = KNOWN_POPULAR.get(ecosystem, frozenset())
    name = normalize_name(name, ecosystem)
    if name in known:
        return None
    allowed = _allowed_distance(name)
    best: str | None = None
    best_distance = allowed + 1
    for candidate in known:
        # A length gap larger than the threshold cannot be within distance.
        if abs(len(candidate) - len(name)) > allowed:
            continue
        distance = _typo_distance(name, candidate)
        if distance < best_distance:
            best_distance = distance
            best = candidate
    if best is not None and 1 <= best_distance <= allowed:
        return best
    return None


def assess_packages(
    command: str,
    registry_fn: Callable[[str, str], bool | None] | None = None,
    budget_seconds: float | None = None,
) -> list[dict[str, str]]:
    """Classify each package an install command would fetch.

    ``registry_fn(name, ecosystem)`` returns True (exists), False
    (definitively absent), or None (could not determine / offline). It
    is only called for names not in the known-popular set. When omitted,
    no registry check is performed and unknown names are left implicit.

    ``budget_seconds`` bounds the total time spent in ``registry_fn``
    across the whole command. Without it a long install list multiplies
    the per-lookup timeout without limit, and a PreToolUse hook killed by
    the harness emits no decision at all, which is the same as no gate:
    the failure lands exactly when a long list makes a hallucinated name
    most likely. Names reached after the budget is spent are reported as
    ``unverified``, which warns and never blocks.

    Returns a list of findings, each a dict with ``name``, ``ecosystem``,
    ``kind`` (``typosquat`` | ``nonexistent`` | ``unverified``), and a
    human-readable ``detail``.
    """
    findings: list[dict[str, str]] = []
    deadline = None if budget_seconds is None else time.monotonic() + budget_seconds
    for ecosystem, name in parse_packages(command):
        known = KNOWN_POPULAR.get(ecosystem, frozenset())
        if normalize_name(name, ecosystem) in known:
            continue

        suspect = nearest_known(name, ecosystem)
        if suspect is not None:
            findings.append(
                {
                    "name": name,
                    "ecosystem": ecosystem,
                    "kind": "typosquat",
                    "detail": (
                        f"'{name}' is one or two edits from the popular "
                        f"package '{suspect}'. Possible typosquat or "
                        f"slopsquat. Confirm the exact name before installing."
                    ),
                }
            )
            continue

        if registry_fn is None:
            continue

        if deadline is not None and time.monotonic() >= deadline:
            findings.append(
                {
                    "name": name,
                    "ecosystem": ecosystem,
                    "kind": "unverified",
                    "detail": (
                        f"Ran out of the registry-lookup budget before "
                        f"reaching '{name}'. Confirm it exists before "
                        f"relying on it."
                    ),
                }
            )
            continue

        exists = registry_fn(name, ecosystem)
        if exists is False:
            findings.append(
                {
                    "name": name,
                    "ecosystem": ecosystem,
                    "kind": "nonexistent",
                    "detail": (
                        f"'{name}' was not found in the {ecosystem} registry. "
                        f"LLM-suggested packages are hallucinated 5-22% of the "
                        f"time; verify the name exists before installing."
                    ),
                }
            )
        elif exists is None:
            findings.append(
                {
                    "name": name,
                    "ecosystem": ecosystem,
                    "kind": "unverified",
                    "detail": (
                        f"Could not reach the {ecosystem} registry to verify "
                        f"'{name}'. Confirm it exists before relying on it."
                    ),
                }
            )
    return findings
