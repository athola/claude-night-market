"""Generate Mermaid and ASCII diagrams from the knowledge graph.

Produces visual representations of palace structure, entity
relationships, and synapse connectivity. Mermaid output can be
rendered via the Mermaid Chart MCP server or displayed in any
Mermaid-compatible viewer.
"""

from __future__ import annotations

import re
from typing import Any

from memory_palace.knowledge_graph import KnowledgeGraph


def _sanitize_label(text: str) -> str:
    """Remove characters that break Mermaid syntax."""
    return re.sub(r'["\[\]{}()|<>]', "", text).strip()


_STRONG_THRESHOLD = 0.7
_MEDIUM_THRESHOLD = 0.4


def _edge_style(strength: float) -> str:
    """Map synapse strength to Mermaid edge syntax."""
    if strength >= _STRONG_THRESHOLD:
        return "==>"  # thick arrow (strong)
    if strength >= _MEDIUM_THRESHOLD:
        return "-->"  # normal arrow (medium)
    return "-.->"  # dotted arrow (weak)


class PalaceRenderer:
    """Render palace structures as Mermaid and ASCII diagrams."""

    def __init__(self, graph: KnowledgeGraph) -> None:
        """Initialize renderer with a knowledge graph."""
        self._graph = graph

    # ------------------------------------------------------------------
    # Mermaid: Palace Map
    # ------------------------------------------------------------------

    def palace_map(self, palace_id: str) -> str:
        """Generate a Mermaid flowchart showing palace rooms and entities."""
        palace = self._graph.get_entity(palace_id)
        if palace is None:
            return ""

        palace_name = _sanitize_label(palace["name"])
        lines = ["flowchart TD"]
        lines.append(f'    palace["{palace_name}"]')

        # Get all residents in this palace
        residents = self._graph.get_residents_in_palace(palace_id)

        # Group residents by room
        rooms: dict[str, list[dict[str, Any]]] = {}
        unroomed: list[dict[str, Any]] = []
        for r in residents:
            room_id = r.get("room_id", "")
            if room_id:
                rooms.setdefault(room_id, []).append(r)
            else:
                unroomed.append(r)

        # Render rooms as subgraphs
        for room_id, room_residents in rooms.items():
            room_entity = self._graph.get_entity(room_id)
            room_name = _sanitize_label(room_entity["name"] if room_entity else room_id)
            lines.append(f"    subgraph {room_id}[{room_name}]")
            for r in room_residents:
                ent = self._graph.get_entity(r["entity_id"])
                if ent and ent["entity_type"] not in ("palace", "room"):
                    ent_label = _sanitize_label(ent["name"])
                    lines.append(f'        {r["entity_id"]}["{ent_label}"]')
            lines.append("    end")
            # Connect palace to room
            lines.append(f"    palace --> {room_id}")

        # Render unroomed entities directly under palace
        for r in unroomed:
            ent = self._graph.get_entity(r["entity_id"])
            if ent and ent["entity_type"] not in ("palace", "room"):
                ent_label = _sanitize_label(ent["name"])
                lines.append(f'    {r["entity_id"]}["{ent_label}"]')
                lines.append(f"    palace --> {r['entity_id']}")

        # Render synapses as edges between entities
        seen_synapses: set[tuple[str, str]] = set()
        for r in residents:
            synapses = self._graph.get_synapses_from(r["entity_id"])
            for syn in synapses:
                pair = (syn["source_id"], syn["target_id"])
                if pair not in seen_synapses:
                    seen_synapses.add(pair)
                    style = _edge_style(syn["strength"])
                    lines.append(f"    {syn['source_id']} {style} {syn['target_id']}")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Mermaid: Entity Relationship Graph
    # ------------------------------------------------------------------

    def entity_graph(self, entity_id: str) -> str:
        """Generate a Mermaid graph showing an entity's connections."""
        entity = self._graph.get_entity(entity_id)
        if entity is None:
            return ""

        ent_label = _sanitize_label(entity["name"])
        lines = ["flowchart LR"]
        lines.append(f'    {entity_id}["{ent_label}"]')

        rendered: set[str] = {entity_id}

        # Outgoing synapses
        for syn in self._graph.get_synapses_from(entity_id):
            target = self._graph.get_entity(syn["target_id"])
            if target and syn["target_id"] not in rendered:
                t_label = _sanitize_label(target["name"])
                lines.append(f'    {syn["target_id"]}["{t_label}"]')
                rendered.add(syn["target_id"])
            style = _edge_style(syn["strength"])
            lines.append(f"    {entity_id} {style} {syn['target_id']}")

        # Incoming synapses
        # Query synapses targeting this entity
        incoming = self._graph._conn.execute(
            "SELECT * FROM synapses WHERE target_id = ?", (entity_id,)
        ).fetchall()
        for syn in incoming:
            source = self._graph.get_entity(syn["source_id"])
            if source and syn["source_id"] not in rendered:
                s_label = _sanitize_label(source["name"])
                lines.append(f'    {syn["source_id"]}["{s_label}"]')
                rendered.add(syn["source_id"])
            style = _edge_style(syn["strength"])
            lines.append(f"    {syn['source_id']} {style} {entity_id}")

        # Triples
        for triple in self._graph.get_active_triples_from(entity_id):
            obj = self._graph.get_entity(triple["object_id"])
            if obj and triple["object_id"] not in rendered:
                o_label = _sanitize_label(obj["name"])
                lines.append(f'    {triple["object_id"]}["{o_label}"]')
                rendered.add(triple["object_id"])
            pred = _sanitize_label(triple["predicate"])
            lines.append(f'    {entity_id} -->|"{pred}"| {triple["object_id"]}')

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Mermaid: Synapse Heatmap
    # ------------------------------------------------------------------

    def synapse_heatmap(self, palace_id: str) -> str:
        """Generate a Mermaid graph with edge styling based on synapse strength."""
        palace = self._graph.get_entity(palace_id)
        if palace is None:
            return ""

        lines = ["flowchart LR"]
        residents = self._graph.get_residents_in_palace(palace_id)
        rendered_nodes: set[str] = set()
        rendered_edges: set[tuple[str, str]] = set()

        for r in residents:
            eid = r["entity_id"]
            for syn in self._graph.get_synapses_from(eid):
                src, tgt = syn["source_id"], syn["target_id"]
                if (src, tgt) in rendered_edges:
                    continue
                rendered_edges.add((src, tgt))

                for nid in (src, tgt):
                    if nid not in rendered_nodes:
                        ent = self._graph.get_entity(nid)
                        if ent:
                            label = _sanitize_label(ent["name"])
                            lines.append(f'    {nid}["{label}"]')
                            rendered_nodes.add(nid)

                style = _edge_style(syn["strength"])
                lines.append(f"    {src} {style} {tgt}")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # ASCII: Palace Overview
    # ------------------------------------------------------------------

    def ascii_overview(self, palace_id: str) -> str:
        """Generate an ASCII box-drawing overview of a palace."""
        palace = self._graph.get_entity(palace_id)
        if palace is None:
            return ""

        palace_name = palace["name"]
        residents = self._graph.get_residents_in_palace(palace_id)

        # Group by room
        rooms: dict[str, list[str]] = {}
        for r in residents:
            room_id = r.get("room_id", "")
            ent = self._graph.get_entity(r["entity_id"])
            if ent and ent["entity_type"] not in ("palace", "room"):
                rooms.setdefault(room_id or "(unassigned)", []).append(ent["name"])

        # Build ASCII output
        lines: list[str] = []
        width = max(
            len(palace_name) + 4,
            *(len(self._room_display_name(rid)) + 10 for rid in rooms),
            30,
        )

        # Palace header
        lines.append("+" + "-" * (width - 2) + "+")
        lines.append("| " + palace_name.center(width - 4) + " |")
        lines.append("+" + "=" * (width - 2) + "+")

        # Rooms
        for room_id, entities in sorted(rooms.items()):
            room_name = self._room_display_name(room_id)
            count = len(entities)
            room_line = f"  {room_name} ({count} entities)"
            lines.append("| " + room_line.ljust(width - 4) + " |")
            for ent_name in entities:
                ent_line = f"    - {ent_name}"
                if len(ent_line) > width - 4:
                    ent_line = ent_line[: width - 7] + "..."
                lines.append("| " + ent_line.ljust(width - 4) + " |")
            lines.append("|" + " " * (width - 2) + "|")

        lines.append("+" + "-" * (width - 2) + "+")

        return "\n".join(lines)

    def _room_display_name(self, room_id: str) -> str:
        """Get display name for a room ID."""
        if room_id == "(unassigned)":
            return room_id
        room = self._graph.get_entity(room_id)
        return room["name"] if room else room_id
