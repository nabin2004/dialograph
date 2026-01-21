"""
Tests for visualization functionality (draw and draw_live).
"""

import pytest
import time
from pathlib import Path
from dialograph import Node, Edge, Dialograph, draw, draw_live


def create_sample_graph():
    """Create a sample graph for testing."""
    graph = Dialograph()
    
    n1 = Node(node_id='n1', node_type='personal_details', data={"value": "Nabin"})
    n2 = Node(node_id='n2', node_type="object", data={"value": "Rice"})
    n3 = Node(node_id='n3', node_type='personal_details', data={"value": "Football"})
    
    e1 = Edge(edge_id='e1', source_node_id='n1', target_node_id='n2', relation='eats')
    e2 = Edge(edge_id='e2', source_node_id='n1', target_node_id='n3', relation='plays')
    
    graph.add_node(n1)
    graph.add_node(n2)
    graph.add_node(n3)
    graph.add_edge(e1)
    graph.add_edge(e2)
    
    return graph


class TestDrawFunction:
    """Tests for the draw() function."""
    
    def test_draw_returns_html_string(self):
        """Test that draw() returns HTML content as a string."""
        graph = create_sample_graph()
        html = draw(graph)
        
        assert isinstance(html, str)
        assert len(html) > 0
        assert "<html>" in html or "<!DOCTYPE html>" in html.lower()
    
    def test_draw_includes_node_labels(self):
        """Test that node labels are included in the output."""
        graph = create_sample_graph()
        html = draw(graph)
        
        # Check that node values appear in the HTML
        assert "Nabin" in html
        assert "Rice" in html
        assert "Football" in html
    
    def test_draw_includes_edge_labels(self):
        """Test that edge labels (relations) are included."""
        graph = create_sample_graph()
        html = draw(graph)
        
        assert "eats" in html
        assert "plays" in html
    
    def test_draw_empty_graph(self):
        """Test that draw() handles empty graphs gracefully."""
        graph = Dialograph()
        html = draw(graph)
        
        assert isinstance(html, str)
        assert len(html) > 0
        assert "Empty Graph" in html
    
    def test_draw_single_node_graph(self):
        """Test that draw() handles single-node graphs."""
        graph = Dialograph()
        node = Node(node_id='n1', node_type='message', data={"value": "Lonely Node"})
        graph.add_node(node)
        
        html = draw(graph)
        
        assert isinstance(html, str)
        assert "Lonely Node" in html
    
    def test_draw_disconnected_components(self):
        """Test that draw() handles disconnected graph components."""
        graph = Dialograph()
        
        # Component 1
        n1 = Node(node_id='n1', node_type='person', data={"value": "Alice"})
        n2 = Node(node_id='n2', node_type='person', data={"value": "Bob"})
        e1 = Edge(edge_id='e1', source_node_id='n1', target_node_id='n2', relation='knows')
        
        # Component 2 (disconnected)
        n3 = Node(node_id='n3', node_type='person', data={"value": "Charlie"})
        n4 = Node(node_id='n4', node_type='person', data={"value": "Dave"})
        e2 = Edge(edge_id='e2', source_node_id='n3', target_node_id='n4', relation='knows')
        
        graph.add_node(n1)
        graph.add_node(n2)
        graph.add_node(n3)
        graph.add_node(n4)
        graph.add_edge(e1)
        graph.add_edge(e2)
        
        html = draw(graph)
        
        assert isinstance(html, str)
        assert "Alice" in html
        assert "Bob" in html
        assert "Charlie" in html
        assert "Dave" in html
    
    def test_draw_determinism(self):
        """Test that draw() produces the same output for the same graph."""
        graph = create_sample_graph()
        
        html1 = draw(graph, physics=False)
        html2 = draw(graph, physics=False)
        
        # With physics disabled, the output should be identical
        assert html1 == html2
    
    def test_draw_custom_colors(self):
        """Test that custom color schemes work."""
        graph = create_sample_graph()
        
        custom_node_colors = {
            "personal_details": "#FF0000",
            "object": "#00FF00",
        }
        
        custom_edge_colors = {
            "eats": "#0000FF",
            "plays": "#FFFF00",
        }
        
        html = draw(graph, node_colors=custom_node_colors, edge_colors=custom_edge_colors)
        
        assert "#FF0000" in html or "rgb(255, 0, 0)" in html or "FF0000" in html
        assert isinstance(html, str)
    
    def test_draw_saves_to_file(self, tmp_path):
        """Test that draw() can save to a file."""
        graph = create_sample_graph()
        output_file = tmp_path / "test_graph.html"
        
        html = draw(graph, filename=str(output_file))
        
        assert output_file.exists()
        assert output_file.read_text() == html
    
    def test_draw_does_not_mutate_graph(self):
        """Test that draw() does not modify the graph state."""
        graph = create_sample_graph()
        
        # Store original state
        original_nodes = dict(graph.nodes)
        original_edges = dict(graph.edges)
        
        # Call draw
        draw(graph)
        
        # Verify graph is unchanged
        assert graph.nodes == original_nodes
        assert graph.edges == original_edges
    
    def test_draw_physics_disabled_by_default(self):
        """Test that physics is disabled by default for deterministic output."""
        graph = create_sample_graph()
        html = draw(graph)
        
        # Check that hierarchical layout is enabled (deterministic)
        assert "hierarchical" in html
        assert isinstance(html, str)


class TestDrawLiveFunction:
    """Tests for the draw_live() function."""
    
    def test_draw_live_returns_server(self):
        """Test that draw_live() returns a server instance."""
        graph = create_sample_graph()
        server = draw_live(graph, open_browser=False)
        
        try:
            assert server is not None
            assert hasattr(server, 'shutdown')
            assert hasattr(server, 'url')
            assert server.is_running()
            assert "http://" in server.url
        finally:
            server.shutdown()
    
    def test_draw_live_auto_assigns_port(self):
        """Test that draw_live() can auto-assign a free port."""
        graph = create_sample_graph()
        server = draw_live(graph, port=0, open_browser=False)
        
        try:
            assert server.url is not None
            assert "127.0.0.1" in server.url or "localhost" in server.url
        finally:
            server.shutdown()
    
    def test_draw_live_custom_port(self):
        """Test that draw_live() respects custom port."""
        graph = create_sample_graph()
        # Use a high port number to avoid conflicts
        custom_port = 9876
        server = draw_live(graph, port=custom_port, open_browser=False)
        
        try:
            assert str(custom_port) in server.url
        finally:
            server.shutdown()
    
    def test_draw_live_shutdown(self):
        """Test that server can be shut down cleanly."""
        graph = create_sample_graph()
        server = draw_live(graph, open_browser=False)
        
        assert server.is_running()
        server.shutdown()
        assert not server.is_running()
    
    def test_draw_live_context_manager(self):
        """Test that draw_live server works as a context manager."""
        graph = create_sample_graph()
        
        with draw_live(graph, open_browser=False) as server:
            assert server.is_running()
        
        # After exiting context, server should be stopped
        assert not server.is_running()
    
    def test_draw_live_does_not_mutate_graph(self):
        """Test that draw_live() does not modify the graph state."""
        graph = create_sample_graph()
        
        # Store original state
        original_nodes = dict(graph.nodes)
        original_edges = dict(graph.edges)
        
        # Call draw_live
        server = draw_live(graph, open_browser=False)
        
        try:
            # Verify graph is unchanged
            assert graph.nodes == original_nodes
            assert graph.edges == original_edges
        finally:
            server.shutdown()
    
    def test_draw_live_empty_graph(self):
        """Test that draw_live() handles empty graphs."""
        graph = Dialograph()
        server = draw_live(graph, open_browser=False)
        
        try:
            assert server.is_running()
        finally:
            server.shutdown()
    
    def test_draw_live_multiple_servers(self):
        """Test that multiple servers can run simultaneously."""
        graph1 = create_sample_graph()
        graph2 = Dialograph()
        n = Node(node_id='n1', node_type='test', data={"value": "Test"})
        graph2.add_node(n)
        
        server1 = draw_live(graph1, port=0, open_browser=False)
        server2 = draw_live(graph2, port=0, open_browser=False)
        
        try:
            assert server1.is_running()
            assert server2.is_running()
            assert server1.url != server2.url  # Different ports
        finally:
            server1.shutdown()
            server2.shutdown()


class TestVisualizationAPIStability:
    """Tests to ensure API stability and backward compatibility."""
    
    def test_draw_backward_compatibility(self):
        """Test that old draw() usage still works (with filename)."""
        graph = create_sample_graph()
        
        # Old-style usage with filename
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name
        
        try:
            html = draw(graph, filename=temp_path)
            assert Path(temp_path).exists()
            assert isinstance(html, str)
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_draw_default_parameters(self):
        """Test that draw() works with minimal parameters."""
        graph = create_sample_graph()
        html = draw(graph)
        assert isinstance(html, str)
    
    def test_draw_live_default_parameters(self):
        """Test that draw_live() works with minimal parameters."""
        graph = create_sample_graph()
        server = draw_live(graph, open_browser=False)
        
        try:
            assert server.is_running()
        finally:
            server.shutdown()
