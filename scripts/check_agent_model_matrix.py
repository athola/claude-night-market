#!/usr/bin/env python3
"""Gate: every agent definition pins an explicit model tier and effort.

Claude Code resolves a subagent's model in this order, first match wins:
``CLAUDE_CODE_SUBAGENT_MODEL`` env var, the per-invocation ``model``
parameter, the agent's ``model:`` frontmatter, then the main
conversation's model. An agent that omits ``model:`` therefore inherits
the session model, so a "cheap background search agent" dispatched from
an Opus session is an Opus agent. Subagents are not free Haiku.

This guard reads every ``plugins/*/agents/*.md`` file and fails when an
agent:

- omits ``model:`` (silent inheritance),
- omits ``effort:`` (untuned reasoning depth),
- pins a dated model ID such as ``claude-sonnet-4-6`` (rots when that
  model generation is retired), or
- uses a value outside the documented vocabulary.

It additionally enforces two things the frontmatter alone cannot:

- ``SKILL.md`` files must not pin a dated model ID either. A skill
  spawns no subagent, so omitting ``model`` is fine there; a dated ID
  still rots.
- ``docs/agent-model-matrix.md`` must document exactly the agents that
  exist. The guide this matrix replaced rotted precisely because a
  hand-maintained agent list had nothing checking it against reality.

Unlike the exit-criteria and skill-graph guards, this is a hard gate
rather than a ratchet. The change that introduced it brought the backlog
to zero, so the illegal state is unrepresentable rather than capped.

Rationale for each assignment lives in ``docs/agent-model-matrix.md``.
The frontmatter is the single source of truth for which tier an agent
sits in; the document carries the reasoning and is checked for roster
drift, never consulted for the tier itself.

Deterministic, read-only, and idempotent.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGINS_ROOT = REPO_ROOT / "plugins"
MATRIX_DOC = "docs/agent-model-matrix.md"

# The three tier aliases Claude Code documents for agent frontmatter.
# ``inherit`` is deliberately excluded: it is the default this gate
# exists to eliminate, so accepting it as an explicit value would defeat
# the purpose.
VALID_MODELS = frozenset({"haiku", "sonnet", "opus"})

# Reasoning-effort levels accepted in agent frontmatter.
VALID_EFFORTS = frozenset({"low", "medium", "high"})

# A dated model ID names a specific generation (``claude-opus-4-1``,
# ``claude-sonnet-4-6``). Those are retired on a rolling basis and the
# alias resolves to the current generation instead.
_DATED_MODEL_RE = re.compile(r"^claude-[a-z]+-\d")

# Matches a top-level ``key: value`` line. Leading whitespace is
# significant: an indented line belongs to a block scalar or a nested
# mapping and must not be read as a top-level field.
_FIELD_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):[ \t]*(.*)$")

# Matches a roster row in the matrix document: a markdown table row whose
# first cell is a backticked ``plugin:agent`` slug. Anchoring on the row
# start keeps prose mentions of the same slug from counting as entries.
_ROSTER_ROW_RE = re.compile(r"^\|\s*`([a-z0-9-]+:[a-z0-9-]+)`\s*\|", re.MULTILINE)


@dataclass(frozen=True)
class AgentViolation:
    """A single rule broken by a single agent file."""

    path: Path
    rule: str
    message: str


def parse_frontmatter(text: str) -> dict[str, str]:
    """Return the top-level scalar fields of a YAML frontmatter fence.

    Only unindented ``key: value`` lines between the opening and closing
    ``---`` fences are returned, which keeps block scalars (``description:
    |``) and nested sequences (``tools:``) from contributing stray keys.
    Values are returned verbatim minus surrounding quotes and whitespace.

    A file with no frontmatter yields an empty mapping.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    fields: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        match = _FIELD_RE.match(line)
        if match is None:
            continue
        key, value = match.group(1), match.group(2).strip()
        fields[key] = value.strip("\"'")
    return fields


def check_agent(path: Path) -> list[AgentViolation]:
    """Return every matrix violation in one agent definition file.

    All rules are evaluated so a single run reports the complete picture
    rather than making the author re-run the gate per field.
    """
    text = path.read_text(encoding="utf-8")
    fields = parse_frontmatter(text)
    violations: list[AgentViolation] = []

    model = fields.get("model")
    if model is None:
        violations.append(
            AgentViolation(
                path,
                "missing-model",
                "no 'model:' in frontmatter, so this agent will inherit the "
                f"session model. Pin one of {sorted(VALID_MODELS)}; see "
                f"{MATRIX_DOC}.",
            )
        )
    elif _DATED_MODEL_RE.match(model):
        violations.append(
            AgentViolation(
                path,
                "dated-model-id",
                f"model '{model}' pins a model generation that will be "
                "retired. Use the tier alias instead "
                f"({sorted(VALID_MODELS)}); see {MATRIX_DOC}.",
            )
        )
    elif model not in VALID_MODELS:
        violations.append(
            AgentViolation(
                path,
                "invalid-model",
                f"model '{model}' is not a recognized tier alias. Use one of "
                f"{sorted(VALID_MODELS)}; see {MATRIX_DOC}.",
            )
        )

    effort = fields.get("effort")
    if effort is None:
        violations.append(
            AgentViolation(
                path,
                "missing-effort",
                "no 'effort:' in frontmatter, so reasoning depth is untuned. "
                f"Pin one of {sorted(VALID_EFFORTS)}; see {MATRIX_DOC}.",
            )
        )
    elif effort not in VALID_EFFORTS:
        violations.append(
            AgentViolation(
                path,
                "invalid-effort",
                f"effort '{effort}' is not a recognized level. Use one of "
                f"{sorted(VALID_EFFORTS)}; see {MATRIX_DOC}.",
            )
        )

    return violations


def check_skill(path: Path) -> list[AgentViolation]:
    """Return dated-model-ID violations in one ``SKILL.md``.

    A skill spawns no subagent, so an absent ``model`` carries none of
    the inheritance hazard that makes it a violation for an agent. Only
    the dated-ID rule applies here.
    """
    fields = parse_frontmatter(path.read_text(encoding="utf-8"))
    model = fields.get("model")
    if model is None or not _DATED_MODEL_RE.match(model):
        return []
    return [
        AgentViolation(
            path,
            "dated-model-id",
            f"model '{model}' pins a model generation that will be retired. "
            f"Use the tier alias instead ({sorted(VALID_MODELS)}), or drop "
            f"the field: a skill spawns nothing, so it need not pin a model.",
        )
    ]


def agent_slug(path: Path) -> str:
    """Return the ``plugin:agent-name`` slug for an agent definition."""
    return f"{path.parent.parent.name}:{path.stem}"


def parse_matrix_roster(doc_text: str) -> set[str]:
    """Return every agent slug listed in the matrix document's tables.

    Only markdown table rows whose first cell is a backticked slug are
    counted, so a slug mentioned in prose is not mistaken for a roster
    entry.
    """
    return set(_ROSTER_ROW_RE.findall(doc_text))


def check_roster_drift(documented: set[str], on_disk: set[str]) -> list[AgentViolation]:
    """Compare the documented roster against the agents that exist.

    Drift is reported in both directions: an agent with no matrix row is
    undocumented, and a matrix row with no agent is stale.
    """
    doc_path = REPO_ROOT / MATRIX_DOC
    violations: list[AgentViolation] = []

    undocumented = sorted(on_disk - documented)
    if undocumented:
        violations.append(
            AgentViolation(
                doc_path,
                "agent-undocumented",
                "these agents exist but have no row in the matrix: "
                f"{', '.join(undocumented)}. Add a row naming the tier and "
                "the reason it sits there.",
            )
        )

    stale = sorted(documented - on_disk)
    if stale:
        violations.append(
            AgentViolation(
                doc_path,
                "roster-stale",
                "the matrix lists agents that no longer exist on disk: "
                f"{', '.join(stale)}. Remove the stale rows.",
            )
        )

    return violations


def iter_agent_files() -> list[Path]:
    """All agent definitions under ``plugins/*/agents/``, venvs excluded."""
    return sorted(
        path
        for path in PLUGINS_ROOT.glob("*/agents/**/*.md")
        if ".venv" not in path.parts
    )


def iter_skill_files() -> list[Path]:
    """All ``SKILL.md`` files under ``plugins/``, venvs excluded."""
    return sorted(
        path for path in PLUGINS_ROOT.rglob("SKILL.md") if ".venv" not in path.parts
    )


def main() -> int:
    """Report every violation and exit non-zero when any exist."""
    agents = iter_agent_files()
    skills = iter_skill_files()

    violations = [violation for path in agents for violation in check_agent(path)]
    violations.extend(violation for path in skills for violation in check_skill(path))

    doc_path = REPO_ROOT / MATRIX_DOC
    if doc_path.exists():
        violations.extend(
            check_roster_drift(
                documented=parse_matrix_roster(doc_path.read_text(encoding="utf-8")),
                on_disk={agent_slug(path) for path in agents},
            )
        )
    else:
        violations.append(
            AgentViolation(
                doc_path,
                "matrix-missing",
                f"{MATRIX_DOC} is missing. It carries the rationale for every "
                "tier assignment and is the reference cited by this gate.",
            )
        )

    if not violations:
        print(
            f"All {len(agents)} agents pin an explicit model and effort, "
            f"{len(skills)} skills carry no dated model IDs, and the matrix "
            f"roster matches disk."
        )
        return 0

    print(f"{len(violations)} agent model/effort violation(s):\n", file=sys.stderr)
    for violation in violations:
        relative = violation.path.relative_to(REPO_ROOT)
        print(f"  {relative}", file=sys.stderr)
        print(f"    [{violation.rule}] {violation.message}", file=sys.stderr)
    print(
        f"\nSubagents inherit the session model when 'model:' is absent. "
        f"Pin every agent to a tier; rationale lives in {MATRIX_DOC}.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
