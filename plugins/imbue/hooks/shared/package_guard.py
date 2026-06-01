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
from collections.abc import Callable

__all__ = [
    "KNOWN_POPULAR",
    "assess_packages",
    "levenshtein",
    "nearest_known",
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
# Targets that are local paths or VCS/URL references, never a registry name.
_NON_REGISTRY_RE = re.compile(r"(^[./~])|(^[a-z]+\+)|(://)|(\.git$)|(^\.$)")

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


def parse_packages(command: str) -> list[tuple[str, str]]:
    """Return ``(ecosystem, name)`` pairs an install command would fetch.

    Versions (``==``, ``@``, ``>=``...), flags, local paths, and VCS
    URLs are stripped. A non-install command returns an empty list.
    """
    text = command.strip()
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

    remainder = text[len(head) :]
    packages: list[tuple[str, str]] = []
    skip_next = False
    for token in remainder.split():
        if skip_next:
            skip_next = False
            continue
        if token in _VALUE_FLAGS:
            skip_next = True
            continue
        if _FLAG_RE.match(token):
            continue
        if _NON_REGISTRY_RE.search(token):
            continue
        name = _strip_version(token)
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
    return re.split(r"[@<>=!~^]", token, maxsplit=1)[0]


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


def nearest_known(name: str, ecosystem: str) -> str | None:
    """Return a popular package this name likely typosquats, else None.

    Returns None when *name* is itself a known-popular package or is too
    distant from every known one to be a plausible typo.
    """
    known = KNOWN_POPULAR.get(ecosystem, frozenset())
    if name in known:
        return None
    best: str | None = None
    best_distance = _TYPOSQUAT_MAX_DISTANCE + 1
    for candidate in known:
        # A length gap larger than the threshold cannot be within distance.
        if abs(len(candidate) - len(name)) > _TYPOSQUAT_MAX_DISTANCE:
            continue
        distance = levenshtein(name, candidate)
        if distance < best_distance:
            best_distance = distance
            best = candidate
    if best is not None and 1 <= best_distance <= _TYPOSQUAT_MAX_DISTANCE:
        return best
    return None


def assess_packages(
    command: str,
    registry_fn: Callable[[str, str], bool | None] | None = None,
) -> list[dict[str, str]]:
    """Classify each package an install command would fetch.

    ``registry_fn(name, ecosystem)`` returns True (exists), False
    (definitively absent), or None (could not determine / offline). It
    is only called for names not in the known-popular set. When omitted,
    no registry check is performed and unknown names are left implicit.

    Returns a list of findings, each a dict with ``name``, ``ecosystem``,
    ``kind`` (``typosquat`` | ``nonexistent`` | ``unverified``), and a
    human-readable ``detail``.
    """
    findings: list[dict[str, str]] = []
    for ecosystem, name in parse_packages(command):
        known = KNOWN_POPULAR.get(ecosystem, frozenset())
        if name in known:
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
