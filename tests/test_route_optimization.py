"""Tests for the graph-based route optimization engine."""

import math

import pytest
import networkx as nx

class TestHaversine:
    """Test haversine distance calculation."""

    def test_lagos_abidjan(self):
        from src.agents.geospatial_intelligence_agent.tools.route_optimization_tool.tool import _haversine
        dist = _haversine(3.40, 6.45, -3.97, 5.36)
        assert 800 < dist < 850  # ~820 km straight line

    def test_same_point(self):
        from src.agents.geospatial_intelligence_agent.tools.route_optimization_tool.tool import _haversine
        assert _haversine(0, 0, 0, 0) == 0.0

    def test_accra_tema(self):
        from src.agents.geospatial_intelligence_agent.tools.route_optimization_tool.tool import _haversine
        dist = _haversine(-0.19, 5.60, 0.00, 5.55)
        assert 15 < dist < 30  # ~21 km
class TestEdgeWeighting:
    """Test priority-based edge weight computation."""

    def test_min_distance_weight(self):
        from src.agents.geospatial_intelligence_agent.tools.route_optimization_tool.tool import _compute_edge_weight
        edge = {"length_km": 10.0, "tier": 1}
        weight = _compute_edge_weight(edge, "min_distance")
        assert weight == 10.0  # pure distance

    def test_min_cost_tier1_cheaper(self):
        from src.agents.geospatial_intelligence_agent.tools.route_optimization_tool.tool import _compute_edge_weight
        tier1 = _compute_edge_weight({"length_km": 10.0, "tier": 1}, "min_cost")
        tier4 = _compute_edge_weight({"length_km": 10.0, "tier": 4}, "min_cost")
        assert tier1 < tier4  # Tier 1 roads are cheaper per km

    def test_balance_produces_valid_weight(self):
        from src.agents.geospatial_intelligence_agent.tools.route_optimization_tool.tool import _compute_edge_weight
        bal = _compute_edge_weight({"length_km": 10.0, "tier": 1}, "balance")
        assert bal > 0
        # Balance for tier 1 should differ from tier 4
        bal4 = _compute_edge_weight({"length_km": 10.0, "tier": 4}, "balance")
        assert bal < bal4  # Tier 1 favored (lower weight)

    def test_max_impact_favors_good_roads(self):
        from src.agents.geospatial_intelligence_agent.tools.route_optimization_tool.tool import _compute_edge_weight
        tier1 = _compute_edge_weight({"length_km": 10.0, "tier": 1}, "max_impact")
        tier4 = _compute_edge_weight({"length_km": 10.0, "tier": 4}, "max_impact")
        assert tier1 < tier4  # Tier 1 favored (lower weight)
class TestGraphNearestNode:
    """Test nearest graph node lookup."""

    def test_find_exact_node(self):
        from src.agents.geospatial_intelligence_agent.tools.route_optimization_tool.tool import _find_nearest_graph_node
        G = nx.Graph()
        G.add_node((3.40, 6.45))
        G.add_node((0.00, 5.55))
        result = _find_nearest_graph_node(G, 3.40, 6.45)
        assert result == (3.40, 6.45)

    def test_find_nearest_not_exact(self):
        from src.agents.geospatial_intelligence_agent.tools.route_optimization_tool.tool import _find_nearest_graph_node
        G = nx.Graph()
        G.add_node((3.40, 6.45))  # Lagos
        G.add_node((0.00, 5.55))  # Tema
        # Point closer to Lagos
        result = _find_nearest_graph_node(G, 3.35, 6.40)
        assert result == (3.40, 6.45)

    def test_no_node_within_range(self):
        from src.agents.geospatial_intelligence_agent.tools.route_optimization_tool.tool import _find_nearest_graph_node
        G = nx.Graph()
        G.add_node((3.40, 6.45))
        # Very far point
        result = _find_nearest_graph_node(G, 100.0, 50.0, max_dist_km=50)
        assert result is None
class TestGraphRouting:
    """Test NetworkX graph-based routing with synthetic road data."""

    @pytest.fixture
    def corridor_graph(self):
        """Build a small test graph simulating corridor roads."""
        G = nx.Graph()
        # Lagos → Cotonou → Lomé → Accra (simplified)
        nodes = [
            (3.40, 6.45),   # Lagos
            (2.42, 6.37),   # Cotonou
            (1.23, 6.17),   # Lomé
            (-0.19, 5.60),  # Accra
        ]
        edges = [
            (nodes[0], nodes[1], {"length_km": 120, "tier": 1, "highway": "motorway", "surface": "asphalt"}),
            (nodes[1], nodes[2], {"length_km": 170, "tier": 2, "highway": "trunk", "surface": "asphalt"}),
            (nodes[2], nodes[3], {"length_km": 200, "tier": 2, "highway": "trunk", "surface": "paved"}),
            # Alternate route: longer but tier 1
            (nodes[0], nodes[3], {"length_km": 550, "tier": 1, "highway": "motorway", "surface": "asphalt"}),
        ]
        for u, v, data in edges:
            G.add_node(u, lon=u[0], lat=u[1])
            G.add_node(v, lon=v[0], lat=v[1])
            G.add_edge(u, v, **data)
        return G

    def test_shortest_path_by_distance(self, corridor_graph):
        for u, v, data in corridor_graph.edges(data=True):
            data["weight"] = data["length_km"]
        path = nx.shortest_path(corridor_graph, (3.40, 6.45), (-0.19, 5.60), weight="weight")
        total = sum(corridor_graph[u][v]["length_km"] for u, v in zip(path[:-1], path[1:]))
        assert total == 490  # 120 + 170 + 200 via intermediate nodes

    def test_shortest_path_by_cost(self, corridor_graph):
        from src.agents.geospatial_intelligence_agent.tools.route_optimization_tool.tool import _compute_edge_weight
        for u, v, data in corridor_graph.edges(data=True):
            data["weight"] = _compute_edge_weight(data, "min_cost")
        path = nx.shortest_path(corridor_graph, (3.40, 6.45), (-0.19, 5.60), weight="weight")
        # Direct tier-1 route (550km × 1.0) vs segmented (120×1.0 + 170×1.5 + 200×1.5 = 675)
        # So direct route should be preferred for min_cost
        assert len(path) == 2  # direct route

    def test_graph_stats(self, corridor_graph):
        from src.pipelines.osm_pipeline.processor import compute_network_stats
        stats = compute_network_stats(corridor_graph)
        assert stats["total_nodes"] == 4
        assert stats["total_edges"] == 4
        assert stats["total_km"] > 0
        assert stats["connected_components"] == 1
class TestOSMProcessor:
    """Test OSM road processing functions."""

    def test_classify_roads(self):
        from src.pipelines.osm_pipeline.processor import classify_roads
        roads = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "properties": {"highway": "motorway", "surface": "asphalt"},
                "geometry": {"type": "LineString", "coordinates": [[3.40, 6.45], [2.63, 6.46]]},
            }],
        }
        result = classify_roads(roads)
        assert result["features"][0]["properties"]["tier"] == 1
        assert result["features"][0]["properties"]["length_km"] > 0

    def test_build_network_graph(self):
        from src.pipelines.osm_pipeline.processor import build_network_graph
        roads = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "properties": {"highway": "trunk", "surface": "paved"},
                "geometry": {"type": "LineString", "coordinates": [[0.0, 5.0], [1.0, 5.5], [2.0, 6.0]]},
            }],
        }
        G = build_network_graph(roads)
        assert G.number_of_nodes() == 3
        assert G.number_of_edges() == 2

    def test_surface_stats(self):
        from src.pipelines.osm_pipeline.processor import classify_roads, compute_surface_stats
        roads = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"highway": "motorway", "surface": "asphalt"},
                    "geometry": {"type": "LineString", "coordinates": [[0, 0], [1, 1]]},
                },
                {
                    "type": "Feature",
                    "properties": {"highway": "track", "surface": "unpaved"},
                    "geometry": {"type": "LineString", "coordinates": [[2, 2], [3, 3]]},
                },
            ],
        }
        classified = classify_roads(roads)
        stats = compute_surface_stats(classified)
        assert "asphalt" in stats
        assert "unpaved" in stats
