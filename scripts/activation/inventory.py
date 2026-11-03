"""FR-1: enumerate the items the model can route a prompt to.

Every rate the suite reports divides by this list, and every comparison
reads its per-item hashes to see which descriptions a change touched.
Only the routed text is hashed: a body edit cannot move routing through
the listing, so it must not look like a change.

The model names a target by id alone, and a command and a skill (or a
workflow) can share one. The harness lists one description per id: in
the session listing observed on 2026-11-03 (Claude Code 2.1.317), all
four shared ids checked showed the workflow text over the command's,
and the command's over the skill's. The hidden files are kept as
``shadowed`` so reports can name descriptions that never reach routing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass, replace
from pathlib import Path

import yaml

_FRONTMATTER = re.compile(r"\A---\n(.*?)\n---", re.DOTALL)
_JS_STRING = r"""'((?:[^'\\]|\\.)*)'|"((?:[^"\\]|\\.)*)\""""


@dataclass(frozen=True)
class Item:
    id: str
    kind: str
    plugin: str
    name: str
    description: str
    path: str
    shadowed: tuple[str, ...] = ()


def normalize(text: str) -> str:
    return " ".join(text.split())


def _frontmatter(path: Path) -> dict:
    match = _FRONTMATTER.match(path.read_text(encoding="utf-8"))
    return yaml.safe_load(match.group(1)) or {} if match else {}


def _js_field(source: str, key: str) -> str | None:
    match = re.search(rf"\b{key}:\s*(?:{_JS_STRING})", source)
    if not match:
        return None
    raw = match.group(1) if match.group(1) is not None else match.group(2)
    return re.sub(r"\\(.)", r"\1", raw)


def _workflow_text(path: Path) -> tuple[dict, str]:
    """Return (flags, routed text). The harness lists `description - whenToUse`."""
    source = path.read_text(encoding="utf-8")
    meta = source[source.index("export const meta") :]
    parts = [_js_field(meta, "description"), _js_field(meta, "whenToUse")]
    disabled = re.search(r"disable-model-invocation['\"]?\s*:\s*true", meta)
    return {"disable-model-invocation": bool(disabled)}, " - ".join(
        p for p in parts if p
    )


PRECEDENCE = {"workflow": 0, "command": 1, "skill": 2}


def build_inventory(root: Path) -> list[Item]:
    items = []
    sources = [
        ("skill", "plugins/*/skills/*/SKILL.md", lambda p: p.parent.name),
        ("command", "plugins/*/commands/*.md", lambda p: p.stem),
        ("workflow", "plugins/*/workflows/*.js", lambda p: p.stem),
    ]
    for kind, pattern, name_of in sources:
        for path in root.glob(pattern):
            if kind == "workflow":
                meta, description = _workflow_text(path)
            else:
                meta = _frontmatter(path)
                description = str(meta.get("description", ""))
            if meta.get("disable-model-invocation") is True:
                continue
            plugin = path.relative_to(root).parts[1]
            name = name_of(path)
            items.append(
                Item(
                    id=f"{plugin}:{name}",
                    kind=kind,
                    plugin=plugin,
                    name=name,
                    description=normalize(description),
                    path=str(path.relative_to(root)),
                )
            )
    by_id: dict[str, list[Item]] = {}
    for item in items:
        by_id.setdefault(item.id, []).append(item)
    merged = []
    for group in by_id.values():
        group.sort(key=lambda i: (PRECEDENCE[i.kind], i.path))
        winner = group[0]
        merged.append(replace(winner, shadowed=tuple(i.path for i in group[1:])))
    return sorted(merged, key=lambda i: i.id)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def item_hashes(items: list[Item]) -> dict[str, str]:
    return {i.id: _sha(i.description) for i in items}


def library_hash(items: list[Item]) -> str:
    return _sha("".join(f"{i.id}\t{i.description}\n" for i in items))


def missing_from_listing(items: list[Item], init_event: dict) -> list[str]:
    """Inventory ids the run's init event did not list (dropped or unloaded)."""
    listed = set(init_event.get("skills", [])) | set(
        init_event.get("slash_commands", [])
    )
    return [i.id for i in items if i.id not in listed]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true", help="print every item")
    args = parser.parse_args(argv)
    items = build_inventory(args.root)
    if args.json:
        json.dump([asdict(i) for i in items], sys.stdout, indent=1)
        sys.stdout.write("\n")
        return 0
    counts = {
        k: sum(i.kind == k for i in items) for k in ("skill", "command", "workflow")
    }
    shadowed = sum(len(i.shadowed) for i in items)
    sys.stdout.write(
        f"{len(items)} routing targets: {counts['skill']} skills, {counts['command']} "
        f"commands, {counts['workflow']} workflows; {shadowed} files shadowed by a "
        f"shared id\nlibrary_hash {library_hash(items)}\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
