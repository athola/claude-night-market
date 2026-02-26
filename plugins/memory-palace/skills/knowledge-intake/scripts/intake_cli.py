#!/usr/bin/env python3
"""Interactive CLI for processing knowledge intake candidates.

Workflow:
1. Load a candidate JSON payload (see docs/templates/intake_candidate.json).
2. Run the Marginal Value Filter to classify redundancy/delta/integration decisions.
3. Prompt the operator (unless --auto-accept) to apply the decision.
4. Generate dual outputs:
   - Palace entry markdown (data/staging)
   - Developer-facing doc stub (docs/developer-drafts)
5. Append an audit row to docs/curation-log.md
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from memory_palace.corpus.marginal_value import (
    IntegrationDecision,
    IntegrationPlan,
    MarginalValueFilter,
)

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
REPO_ROOT = PLUGIN_ROOT.parents[1]
PROMPT_TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "prompts"
DEFAULT_PROMPT_PACK = "marginal-value-dual"


@dataclass
class Candidate:
    """Parsed intake candidate with convenience accessors."""

    raw: dict[str, Any]
    content: str

    @property
    def title(self) -> str:
        """Return candidate title or fallback."""
        summary = self.raw.get("summary", {})
        return summary.get("title") or "Untitled Intake Candidate"

    @property
    def tags(self) -> list[str]:
        """Return candidate tags."""
        summary = self.raw.get("summary", {})
        return summary.get("tags") or []

    @property
    def actor(self) -> str:
        """Reviewer identifier from audit metadata."""
        audit = self.raw.get("audit", {})
        return audit.get("reviewed_by") or os.getenv("USER", "unknown")

    @property
    def autonomy_level(self) -> int:
        """Autonomy level of the candidate."""
        evaluation = self.raw.get("evaluation", {})
        return int(evaluation.get("autonomy_level", 0))

    @property
    def source_identifier(self) -> str:
        """Source identifier for traceability."""
        source = self.raw.get("source", {})
        return source.get("identifier", "unknown")


def slugify(value: str) -> str:
    """Convert a string to a filesystem-safe slug."""
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in value)
    slug = "-".join(filter(None, slug.split("-")))
    return slug or "intake-entry"


def load_candidate(path: Path) -> Candidate:
    """Load candidate JSON file into Candidate object."""
    data = json.loads(path.read_text(encoding="utf-8"))
    content = data.get("content")
    if not content:
        content_path = data.get("content_path")
        if not content_path:
            raise ValueError("candidate requires `content` or `content_path`")
        content = Path(content_path).read_text(encoding="utf-8")
    return Candidate(raw=data, content=content)


def ensure_dirs(path: Path) -> None:
    """Validate parent directory exists."""
    path.parent.mkdir(parents=True, exist_ok=True)


def write_palace_entry(
    root: Path,
    candidate: Candidate,
    decision: IntegrationDecision,
    slug: str,
    confidence: float | None,
) -> Path:
    """Write palace entry markdown for a candidate."""
    palace_dir = root / "data" / "staging"
    palace_path = palace_dir / f"{slug}.md"
    ensure_dirs(palace_path)

    fm = {
        "title": candidate.title,
        "source": candidate.raw.get("source", {}),
        "author": candidate.actor,
        "date_captured": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d"),
        "palace": candidate.raw.get("summary", {}).get("palace", "Intake"),
        "district": candidate.raw.get("summary", {}).get("district", "Curation"),
        "maturity": "probation",
        "tags": candidate.tags,
    }
    header = yaml.safe_dump(fm, sort_keys=False).strip()
    conf_display = f"{confidence:.0%}" if isinstance(confidence, float) else "n/a"
    body = (
        f"---\n{header}\n---\n\n"
        f"# {candidate.title}\n\n"
        "## Marginal Value Summary\n\n"
        f"- **Integration Decision**: {decision.value}\n"
        f"- **Confidence**: {conf_display}\n"
        f"- **Novelty Tags**: {', '.join(candidate.tags) or 'n/a'}\n\n"
        "## Intake Content\n\n"
        f"{candidate.content.strip()}\n"
    )
    palace_path.write_text(body, encoding="utf-8")
    return palace_path


def write_developer_doc(
    root: Path, candidate: Candidate, slug: str, palace_path: Path
) -> Path:
    """Write a developer-facing draft doc for the intake candidate."""
    drafts_dir = root / "docs" / "developer-drafts"
    doc_path = drafts_dir / f"{slug}.md"
    ensure_dirs(doc_path)
    content = f"""# Developer Notes — {candidate.title}

- **Source**: {candidate.source_identifier}
- **Palace Entry**: {palace_path.relative_to(root)}
- **Tags**: {", ".join(candidate.tags) or "n/a"}

## Summary

{candidate.content.strip()[:500]}...

## Next Steps

1. Integrate knowledge into relevant README/tutorial.
2. Add regression tests/docs references as needed.
"""
    doc_path.write_text(content, encoding="utf-8")
    return doc_path


def render_prompt_template(template: str, context: dict[str, str]) -> str:
    """Render a prompt template by replacing context placeholders."""
    rendered = template
    for key, value in context.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
        rendered = rendered.replace(f"{{{{ {key} }}}}", value)
    return rendered


def load_prompt_template(prompt_pack: str) -> str:
    """Load prompt template content from the prompts directory."""
    normalized = prompt_pack.strip().lower()
    candidates = [
        normalized.replace("-", "_"),
        normalized,
    ]
    for name in candidates:
        template_path = PROMPT_TEMPLATE_DIR / f"{name}.md"
        if template_path.exists():
            return template_path.read_text(encoding="utf-8")
    expected = [f"{name}.md" for name in candidates]
    raise FileNotFoundError(
        f"No prompt template found for '{prompt_pack}'. Expected one of {expected}"
    )


def write_prompt_pack(
    output_root: Path,
    prompt_pack: str,
    candidate: Candidate,
    integration: IntegrationPlan,
) -> Path:
    """Write a prompt pack markdown file using rendered template."""
    template = load_prompt_template(prompt_pack)
    tags = ", ".join(candidate.tags) if candidate.tags else "n/a"
    summary = candidate.raw.get("summary", {})
    context = {
        "title": candidate.title,
        "source": candidate.source_identifier,
        "tags": tags,
        "palace": summary.get("palace", "Knowledge Brain"),
        "district": summary.get("district", "Curation"),
        "integration_decision": integration.decision.value,
        "integration_confidence": (
            f"{integration.confidence:.0%}"
            if isinstance(integration.confidence, float)
            else "n/a"
        ),
        "autonomy_level": str(candidate.autonomy_level),
        "actor": candidate.actor,
        "content": candidate.content.strip(),
    }
    rendered = render_prompt_template(template, context)
    prompt_slug = prompt_pack.strip().lower().replace("_", "-")
    prompt_dir = output_root / "docs" / "prompts"
    prompt_path = prompt_dir / f"{prompt_slug}.md"
    ensure_dirs(prompt_path)
    prompt_path.write_text(rendered, encoding="utf-8")
    return prompt_path


def append_curation_log(  # noqa: PLR0913 - log needs explicit context fields
    log_path: Path,
    candidate: Candidate,
    decision: IntegrationDecision,
    palace_path: Path,
    dev_doc: Path,
    prompt_path: Path | None = None,
    prompt_pack: str | None = None,
) -> None:
    """Append a Markdown table row to the curation log."""
    ensure_dirs(log_path)
    if not log_path.exists():
        log_path.write_text(
            "| Timestamp | Actor | Source | Decision | Autonomy Level | Notes |\n"
            "|-----------|-------|--------|----------|----------------|-------|\n",
            encoding="utf-8",
        )
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    notes_parts = [
        f"title:{candidate.title}",
        f"palace:{palace_path.name}",
        f"dev:{dev_doc.name}",
    ]
    if prompt_path:
        prompt_label = prompt_pack or prompt_path.stem
        notes_parts.append(f"prompt:{prompt_label}")
    notes = ", ".join(notes_parts)
    row = (
        f"| {timestamp} | {candidate.actor} | {candidate.source_identifier} | "
        f"{decision.value} | {candidate.autonomy_level} | {notes} |\n"
    )
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(row)


def process_candidate(  # noqa: PLR0913 - CLI surface mirrors command options
    candidate_path: Path,
    corpus_dir: Path,
    index_dir: Path,
    output_root: Path,
    curation_log: Path,
    auto_accept: bool,
    dual_output: bool = False,
    prompt_pack: str | None = None,
) -> dict[str, Any]:  # noqa: PLR0913 - CLI command surface requires these args
    """Process an intake candidate end-to-end and write outputs."""
    candidate = load_candidate(candidate_path)
    mv_filter = MarginalValueFilter(str(corpus_dir), str(index_dir))
    redundancy, delta, integration = mv_filter.evaluate_content(
        candidate.content, candidate.title, candidate.tags
    )

    summary = {
        "redundancy": redundancy.level.value,
        "overlap": redundancy.overlap_score,
        "integration": integration.decision.value,
        "confidence": integration.confidence,
        "novelty_score": delta.value_score if delta else None,
    }

    print(f"[Intake] {candidate.title}")
    print(f"  Redundancy: {redundancy.level.value} ({redundancy.overlap_score:.0%})")
    if delta:
        print(f"  Delta type: {delta.delta_type.value} value {delta.value_score:.0%}")
    print(
        f"  Integration decision: {integration.decision.value} ({integration.confidence:.0%})"
    )

    if integration.decision == IntegrationDecision.SKIP:
        summary["status"] = "skipped"
        return summary

    if not auto_accept:
        resp = input("Apply this decision? [y/N]: ").strip().lower()
        if resp not in {"y", "yes"}:
            summary["status"] = "aborted"
            return summary

    slug = slugify(candidate.title)
    palace_path = write_palace_entry(
        output_root, candidate, integration.decision, slug, integration.confidence
    )
    dev_doc_path = write_developer_doc(output_root, candidate, slug, palace_path)
    prompt_slug: str | None = None
    prompt_path: Path | None = None
    if dual_output:
        pack_value = (prompt_pack or DEFAULT_PROMPT_PACK).strip() or DEFAULT_PROMPT_PACK
        prompt_slug = pack_value.lower().replace("_", "-")
        prompt_path = write_prompt_pack(
            output_root, prompt_slug, candidate, integration
        )
        summary["prompt_pack"] = prompt_slug
        summary["prompt_path"] = str(prompt_path)
    append_curation_log(
        curation_log,
        candidate,
        integration.decision,
        palace_path,
        dev_doc_path,
        prompt_path=prompt_path,
        prompt_pack=prompt_slug,
    )

    summary["status"] = "applied"
    summary["palace_entry"] = str(palace_path)
    summary["developer_doc"] = str(dev_doc_path)
    return summary


def main(argv: list[str] | None = None) -> None:
    """CLI entrypoint for processing knowledge intake candidates."""
    parser = argparse.ArgumentParser(description="Process knowledge intake candidates")
    parser.add_argument(
        "--candidate", required=True, type=Path, help="Path to intake_candidate.json"
    )
    parser.add_argument(
        "--corpus-dir", type=Path, default=PLUGIN_ROOT / "data" / "staging"
    )
    parser.add_argument(
        "--index-dir", type=Path, default=PLUGIN_ROOT / "data" / "indexes"
    )
    parser.add_argument("--output-root", type=Path, default=PLUGIN_ROOT)
    parser.add_argument(
        "--curation-log",
        type=Path,
        default=REPO_ROOT / "docs" / "curation-log.md",
        help="Path to curation log markdown file",
    )
    parser.add_argument(
        "--auto-accept", action="store_true", help="Apply decision without prompt"
    )
    parser.add_argument(
        "--dual-output",
        action="store_true",
        help="Emit both palace/developer artifacts and a prompt-pack handoff",
    )
    parser.add_argument(
        "--prompt-pack",
        type=str,
        default=None,
        help="Slug for the prompt pack template (defaults to marginal-value-dual)",
    )
    args = parser.parse_args(argv)

    summary = process_candidate(
        candidate_path=args.candidate,
        corpus_dir=args.corpus_dir,
        index_dir=args.index_dir,
        output_root=args.output_root,
        curation_log=args.curation_log,
        auto_accept=args.auto_accept,
        dual_output=args.dual_output,
        prompt_pack=args.prompt_pack,
    )

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
