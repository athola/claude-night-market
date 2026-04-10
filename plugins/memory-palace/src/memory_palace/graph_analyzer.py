"""NetworkX-based graph analysis for palace knowledge graphs.

Loads the SQLite knowledge graph into a NetworkX DiGraph and
runs algorithms for tier scoring, community detection, bridge
identification, shortest paths, and link prediction.
"""

from __future__ import annotations

import networkx as nx  # type: ignore[import-untyped]  # networkx lacks py.typed marker

from memory_palace.knowledge_graph import KnowledgeGraph


class PalaceGraphAnalyzer:
    """Analyze palace knowledge graphs using NetworkX algorithms."""

    def __init__(self, graph: KnowledgeGraph) -> None:
        """Initialize analyzer with a knowledge graph."""
        self._kg = graph
        self._nx: nx.DiGraph | None = None

    def build_graph(self) -> nx.DiGraph:
        """Load the knowledge graph into a NetworkX DiGraph."""
        dg = nx.DiGraph()

        entities = self._kg._conn.execute(
            "SELECT entity_id, entity_type, name FROM entities"
        ).fetchall()
        for e in entities:
            dg.add_node(e["entity_id"], entity_type=e["entity_type"], name=e["name"])

        synapses = self._kg._conn.execute(
            "SELECT source_id, target_id, strength FROM synapses"
        ).fetchall()
        for s in synapses:
            dg.add_edge(s["source_id"], s["target_id"], weight=s["strength"])

        self._nx = dg
        return dg

    def _ensure_graph(self) -> nx.DiGraph:
        if self._nx is None:
            return self.build_graph()
        return self._nx

    # ------------------------------------------------------------------
    # PageRank
    # ------------------------------------------------------------------

    def pagerank(self) -> dict[str, float]:
        """Compute PageRank for all entities. Returns normalized scores."""
        dg = self._ensure_graph()
        if len(dg.nodes) == 0:
            return {}
        result: dict[str, float] = nx.pagerank(dg, weight="weight")
        return result

    # ------------------------------------------------------------------
    # Betweenness Centrality
    # ------------------------------------------------------------------

    def betweenness_centrality(self) -> dict[str, float]:
        """Compute betweenness centrality for all entities."""
        dg = self._ensure_graph()
        if len(dg.nodes) == 0:
            return {}
        result: dict[str, float] = nx.betweenness_centrality(dg, weight="weight")
        return result

    # ------------------------------------------------------------------
    # Community Detection
    # ------------------------------------------------------------------

    def detect_communities(self) -> dict[int, set[str]]:
        """Detect communities using greedy modularity on undirected view.

        Returns a dict mapping community ID to set of entity IDs.
        """
        dg = self._ensure_graph()
        if len(dg.nodes) == 0:
            return {}

        ug = dg.to_undirected()
        communities = nx.community.greedy_modularity_communities(ug, weight="weight")

        result: dict[int, set[str]] = {}
        for idx, comm in enumerate(communities):
            result[idx] = set(comm)
        return result

    # ------------------------------------------------------------------
    # Structural Analysis
    # ------------------------------------------------------------------

    def find_bridges(self) -> list[tuple[str, str]]:
        """Find bridge edges (removal disconnects the graph).

        Works on the undirected view since bridges are defined
        for undirected graphs.
        """
        dg = self._ensure_graph()
        ug = dg.to_undirected()
        return list(nx.bridges(ug))

    def find_keystones(self) -> list[str]:
        """Find articulation points (keystone entities).

        Removal of a keystone disconnects the undirected graph.
        """
        dg = self._ensure_graph()
        ug = dg.to_undirected()
        return list(nx.articulation_points(ug))

    def connected_components(self) -> list[set[str]]:
        """Find connected components in the undirected view."""
        dg = self._ensure_graph()
        ug = dg.to_undirected()
        return [set(c) for c in nx.connected_components(ug)]

    # ------------------------------------------------------------------
    # Shortest Path
    # ------------------------------------------------------------------

    def shortest_path(self, source: str, target: str) -> list[str] | None:
        """Find the shortest weighted path between two entities.

        Uses inverse weight (1/strength) so stronger synapses
        are preferred. Returns None if no path exists.
        """
        dg = self._ensure_graph()
        if source not in dg or target not in dg:
            return None

        # Invert weights so stronger synapses = lower cost = preferred
        weighted = dg.copy()
        for _u, _v, data in weighted.edges(data=True):
            w = data.get("weight", 0.1)
            data["inv_weight"] = 1.0 / max(w, 0.01)

        try:
            path: list[str] = nx.shortest_path(
                weighted, source, target, weight="inv_weight"
            )
            return path
        except nx.NetworkXNoPath:
            return None

    # ------------------------------------------------------------------
    # Link Prediction
    # ------------------------------------------------------------------

    def predict_links(self, top_n: int = 10) -> list[tuple[str, str, float]]:
        """Predict missing links using Adamic-Adar index.

        Returns top_n (source, target, score) tuples for
        non-existing edges, sorted by score descending.
        """
        dg = self._ensure_graph()
        ug = dg.to_undirected()

        min_nodes_for_prediction = 2
        if len(ug.nodes) < min_nodes_for_prediction:
            return []

        non_edges = list(nx.non_edges(ug))
        if not non_edges:
            return []

        preds = nx.adamic_adar_index(ug, non_edges)
        scored = [(u, v, s) for u, v, s in preds if s > 0]
        scored.sort(key=lambda x: x[2], reverse=True)
        return scored[:top_n]
