import os
import time
import pickle
import pytest
import networkx as nx

from dialograph import Dialograph, Node, Edge

def make_node(node_id):
    return Node(node_id=node_id, node_type="message")

def make_edge(edge_id, src, dst, created_at=None):
    return Edge(
        edge_id=edge_id,
        source_node_id=src,
        target_node_id=dst,
        relation="supports",
        created_at=created_at or time.time()
    )

def test_graph_initialization():
    g = Dialograph()
    assert isinstance(g.graph, nx.MultiDiGraph)
    assert g.nodes == {}
    assert g.edges == {}
    assert g.time == 0

def test_graph_step_increments_time():
    g = Dialograph()
    t1 = g.step()
    t2 = g.step()
    assert t1 == 1
    assert t2 == 2
    assert g.time == 2


def test_add_and_get_node():
    g = Dialograph()
    node = make_node("n1")
    g.add_node(node)

    assert "n1" in g.nodes
    assert g.get_node("n1") is node
    assert g.graph.has_node("n1")

def test_add_duplicate_node_raises():
    g = Dialograph()
    node = make_node("n1")
    g.add_node(node)
    with pytest.raises(ValueError):
        g.add_node(node)

def test_add_edge_success():
    g = Dialograph()
    n1 = make_node("n1")
    n2 = make_node("n2")
    g.add_node(n1)
    g.add_node(n2)

    edge = make_edge("e1", "n1", "n2")
    g.add_edge(edge)

    assert "e1" in g.edges
    assert g.edges["e1"] is edge
    # verify edge exists in networkx graph
    assert g.graph.has_edge("n1", "n2", key="e1")

def test_add_edge_missing_nodes_raises():
    g = Dialograph()
    n1 = make_node("n1")
    g.add_node(n1)

    # target missing
    edge = make_edge("e1", "n1", "n2")
    with pytest.raises(ValueError):
        g.add_edge(edge)

    # source missing
    edge2 = make_edge("e2", "n2", "n1")
    with pytest.raises(ValueError):
        g.add_edge(edge2)

def test_add_duplicate_edge_raises():
    g = Dialograph()
    n1 = make_node("n1")
    n2 = make_node("n2")
    g.add_node(n1)
    g.add_node(n2)

    edge = make_edge("e1", "n1", "n2")
    g.add_edge(edge)

    # duplicate edge
    edge2 = make_edge("e1", "n1", "n2")
    with pytest.raises(ValueError):
        g.add_edge(edge2)


def test_get_edges_returns_correct_list():
    g = Dialograph()
    n1 = make_node("n1")
    n2 = make_node("n2")
    g.add_node(n1)
    g.add_node(n2)

    edge1 = make_edge("e1", "n1", "n2")
    edge2 = make_edge("e2", "n1", "n2")
    g.add_edge(edge1)
    g.add_edge(edge2)

    edges = g.get_edges("n1", "n2")
    assert set(e.edge_id for e in edges) == {"e1", "e2"}

def test_get_edges_returns_correct_list():
    g = Dialograph()
    n1 = make_node("n1")
    n2 = make_node("n2")
    g.add_node(n1)
    g.add_node(n2)

    edge1 = make_edge("e1", "n1", "n2")
    edge2 = make_edge("e2", "n1", "n2")
    g.add_edge(edge1)
    g.add_edge(edge2)

    edges = g.get_edges("n1", "n2")
    assert set(e.edge_id for e in edges) == {"e1", "e2"}

