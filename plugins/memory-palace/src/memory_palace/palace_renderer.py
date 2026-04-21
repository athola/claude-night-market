"""Generate Mermaid and ASCII diagrams from the knowledge graph.

Produces visual representations of palace structure, entity
relationships, and synapse connectivity. Mermaid output can be
rendered via the Mermaid Chart MCP server or displayed in any
Mermaid-compatible viewer.
"""

from __future__ import annotations

import json
import re
from typing import Any

from memory_palace.knowledge_graph import KnowledgeGraph

try:
    from memory_palace.graph_analyzer import PalaceGraphAnalyzer as _PalaceGraphAnalyzer

    _ANALYZER_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    _ANALYZER_AVAILABLE = False
    _PalaceGraphAnalyzer = None  # type: ignore[assignment,misc]  # None sentinel replaces class when graph_analyzer unavailable


def _sanitize_label(text: str) -> str:
    """Remove characters that break Mermaid syntax."""
    return re.sub(r'["\[\]{}()|<>]', "", text).strip()


_STRONG_THRESHOLD = 0.7
_MEDIUM_THRESHOLD = 0.4

# PageRank thresholds for node shape selection in algo_informed_er_graph
_PAGERANK_STADIUM_THRESHOLD = 0.2  # score >= this → stadium shape ([name])
_PAGERANK_ROUND_THRESHOLD = 0.1  # score >= this → round shape (name)


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

    # ------------------------------------------------------------------
    # Mermaid: Journey Replay (Issue #392)
    # ------------------------------------------------------------------

    def journey_replay(self, entity_id: str) -> str:
        """Generate a Mermaid sequenceDiagram showing entity journey.

        Queries journey tracker data for waypoints of the given entity.
        Each waypoint is rendered as a sequence event with the palace
        as participant. State deltas appear as notes.

        Returns empty string if no journey data exists.
        """
        rows = self._graph._conn.execute(
            """SELECT j.id AS journey_id, j.trigger,
                      w.sequence, w.palace_id, w.entity_delta
               FROM journeys j
               JOIN waypoints w ON w.journey_id = j.id
               WHERE j.entity_id = ?
               ORDER BY j.id, w.sequence""",
            (entity_id,),
        ).fetchall()

        if not rows:
            return ""

        lines = ["sequenceDiagram"]
        lines.append(f"    participant entity AS {_sanitize_label(entity_id)}")

        seen_palaces: set[str] = set()
        for row in rows:
            palace_id = row["palace_id"]
            if palace_id not in seen_palaces:
                seen_palaces.add(palace_id)
                palace_ent = self._graph.get_entity(palace_id)
                palace_label = (
                    _sanitize_label(palace_ent["name"])
                    if palace_ent
                    else _sanitize_label(palace_id)
                )
                lines.append(f"    participant {palace_id} AS {palace_label}")

        for row in rows:
            palace_id = row["palace_id"]
            lines.append(f"    entity->>{palace_id}: visit")

            # Render state delta as a note if non-empty
            delta_str = row["entity_delta"] or "{}"
            try:
                delta = json.loads(delta_str)
            except (ValueError, TypeError):
                delta = {}

            if delta:
                delta_text = ", ".join(f"{k}={v}" for k, v in list(delta.items())[:3])
                lines.append(
                    f"    Note over {palace_id}: {_sanitize_label(delta_text)}"
                )

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Mermaid: Temporal View (Issue #392)
    # ------------------------------------------------------------------

    def temporal_view(self, palace_id: str, at_time: str) -> str:
        """Generate a Mermaid flowchart TD for triples active at a timestamp.

        Filters triples by valid_from / valid_to fields, treating empty
        string or NULL as unbounded (no constraint on that end).

        Returns empty string if no active triples exist in the palace.
        """
        palace = self._graph.get_entity(palace_id)
        if palace is None:
            return ""

        # Collect entity IDs in this palace
        residents = self._graph.get_residents_in_palace(palace_id)
        resident_ids = {r["entity_id"] for r in residents}
        # Include the palace entity itself
        resident_ids.add(palace_id)

        # Find triples where both subject and object are in the palace,
        # applying temporal filter:
        #   valid_from = '' OR valid_from IS NULL OR valid_from <= at_time
        #   AND (valid_to = '' OR valid_to IS NULL OR valid_to > at_time)
        active_triples = self._graph._conn.execute(
            """SELECT * FROM triples
               WHERE (valid_from = '' OR valid_from IS NULL OR valid_from <= ?)
                 AND (valid_to = '' OR valid_to IS NULL OR valid_to > ?)""",
            (at_time, at_time),
        ).fetchall()

        # Filter to only triples involving palace residents
        filtered = [
            t
            for t in active_triples
            if t["subject_id"] in resident_ids or t["object_id"] in resident_ids
        ]

        if not filtered:
            return ""

        lines = ["flowchart TD"]
        rendered: set[str] = set()

        for triple in filtered:
            subj_id = triple["subject_id"]
            obj_id = triple["object_id"]

            for eid in (subj_id, obj_id):
                if eid not in rendered:
                    ent = self._graph.get_entity(eid)
                    if ent:
                        label = _sanitize_label(ent["name"])
                        lines.append(f'    {eid}["{label}"]')
                    else:
                        lines.append(f'    {eid}["{_sanitize_label(eid)}"]')
                    rendered.add(eid)

            pred = _sanitize_label(triple["predicate"])
            lines.append(f'    {subj_id} -->|"{pred}"| {obj_id}')

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Mermaid: Algorithm-Informed ER Graph (Issue #392)
    # ------------------------------------------------------------------

    def algo_informed_er_graph(self, palace_id: str) -> str:
        """Generate a Mermaid flowchart LR with algorithm-informed layout.

        Uses PageRank for node shapes, community detection for subgraphs,
        articulation points for CSS keystone class, and bridge edges for
        thick rendering. Falls back gracefully if analyzer unavailable.
        """
        palace = self._graph.get_entity(palace_id)
        if palace is None:
            return ""

        try:
            if not _ANALYZER_AVAILABLE or _PalaceGraphAnalyzer is None:
                return self._plain_er_graph(palace_id)
            analyzer = _PalaceGraphAnalyzer(self._graph)
            pagerank_scores = analyzer.pagerank()
            communities = analyzer.detect_communities()
            keystones: set[str] = set(analyzer.find_keystones())
            bridges: set[tuple[str, str]] = set(analyzer.find_bridges())
        except Exception:
            # Degrade to plain entity_graph-style output
            return self._plain_er_graph(palace_id)

        residents = self._graph.get_residents_in_palace(palace_id)
        if not residents:
            return self._plain_er_graph(palace_id)

        resident_ids = {r["entity_id"] for r in residents}
        comm_map, entity_to_comm = self._build_community_map(communities, resident_ids)
        unassigned = [eid for eid in resident_ids if eid not in entity_to_comm]

        lines = ["flowchart LR"]
        rendered_nodes: set[str] = set()

        self._render_community_subgraphs(
            lines, rendered_nodes, comm_map, keystones, pagerank_scores
        )
        self._render_unassigned_nodes(
            lines, rendered_nodes, unassigned, keystones, pagerank_scores
        )
        self._render_algo_edges(lines, residents, bridges)

        if keystones & resident_ids:
            lines.append("    classDef keystone fill:#f96")

        return "\n".join(lines)

    def _build_community_map(
        self,
        communities: dict[int, set[str]],
        resident_ids: set[str],
    ) -> tuple[dict[int, list[str]], dict[str, int]]:
        """Map community IDs to palace-resident entity lists."""
        comm_map: dict[int, list[str]] = {}
        entity_to_comm: dict[str, int] = {}
        for cid, comm_members in communities.items():
            palace_members = [m for m in comm_members if m in resident_ids]
            if palace_members:
                comm_map[cid] = palace_members
                for eid in palace_members:
                    entity_to_comm[eid] = cid
        return comm_map, entity_to_comm

    def _er_node_line(
        self,
        eid: str,
        pagerank_scores: dict[str, float],
        keystones: set[str],
    ) -> str:
        """Return a Mermaid node line with shape and optional keystone class."""
        score = pagerank_scores.get(eid, 0.0)
        label = _sanitize_label((self._graph.get_entity(eid) or {}).get("name", eid))
        if score >= _PAGERANK_STADIUM_THRESHOLD:
            base = f"    {eid}([{label}])"
        elif score >= _PAGERANK_ROUND_THRESHOLD:
            base = f"    {eid}({label})"
        else:
            base = f'    {eid}["{label}"]'
        return base + ":::keystone" if eid in keystones else base

    def _render_community_subgraphs(
        self,
        lines: list[str],
        rendered_nodes: set[str],
        comm_map: dict[int, list[str]],
        keystones: set[str],
        pagerank_scores: dict[str, float],
    ) -> None:
        """Append community subgraph blocks to lines."""
        _non_structural = ("palace", "room")
        for comm_id, comm_entity_list in sorted(comm_map.items()):
            lines.append(f"    subgraph cluster_{comm_id}[Community {comm_id}]")
            for eid in comm_entity_list:
                ent = self._graph.get_entity(eid)
                if ent and ent.get("entity_type") not in _non_structural:
                    lines.append(self._er_node_line(eid, pagerank_scores, keystones))
                    rendered_nodes.add(eid)
            lines.append("    end")

    def _render_unassigned_nodes(
        self,
        lines: list[str],
        rendered_nodes: set[str],
        unassigned: list[str],
        keystones: set[str],
        pagerank_scores: dict[str, float],
    ) -> None:
        """Append unassigned entity nodes to lines."""
        _non_structural = ("palace", "room")
        for eid in unassigned:
            if eid in rendered_nodes:
                continue
            ent = self._graph.get_entity(eid)
            if ent and ent.get("entity_type") not in _non_structural:
                lines.append(self._er_node_line(eid, pagerank_scores, keystones))
                rendered_nodes.add(eid)

    def _render_algo_edges(
        self,
        lines: list[str],
        residents: list[dict[str, Any]],
        bridges: set[tuple[str, str]],
    ) -> None:
        """Append synapse edges with bridge rendering to lines."""
        bridge_set = bridges | {(b, a) for a, b in bridges}
        seen_edges: set[tuple[str, str]] = set()
        for r in residents:
            for syn in self._graph.get_synapses_from(r["entity_id"]):
                src, tgt = syn["source_id"], syn["target_id"]
                if (src, tgt) in seen_edges:
                    continue
                seen_edges.add((src, tgt))
                if (src, tgt) in bridge_set:
                    lines.append(f"    {src} ==== {tgt}")
                else:
                    lines.append(f"    {src} {_edge_style(syn['strength'])} {tgt}")

    def _plain_er_graph(self, palace_id: str) -> str:
        """Fallback plain ER graph (entity_graph style) for palace residents."""
        palace = self._graph.get_entity(palace_id)
        if palace is None:
            return ""

        lines = ["flowchart LR"]
        residents = self._graph.get_residents_in_palace(palace_id)
        rendered_nodes: set[str] = set()
        seen_edges: set[tuple[str, str]] = set()

        for r in residents:
            eid = r["entity_id"]
            ent = self._graph.get_entity(eid)
            if ent and ent.get("entity_type") not in ("palace", "room"):
                if eid not in rendered_nodes:
                    label = _sanitize_label(ent["name"])
                    lines.append(f'    {eid}["{label}"]')
                    rendered_nodes.add(eid)
                for syn in self._graph.get_synapses_from(eid):
                    src, tgt = syn["source_id"], syn["target_id"]
                    if (src, tgt) not in seen_edges:
                        seen_edges.add((src, tgt))
                        style = _edge_style(syn["strength"])
                        lines.append(f"    {src} {style} {tgt}")

        return "\n".join(lines)
