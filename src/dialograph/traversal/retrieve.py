import networkx as nx
from typing import List, Optional


def retrieve_neighbors(
    graph,
    source_node_id: str,
    now: float,
    top_k: int = 5,
    context_match_fn=None,
):
    scored = []

    for edge in graph.out_edges(source_node_id):
        neighbor = graph.get_node(edge.target_node_id)

        context_match = (
            context_match_fn(neighbor) if context_match_fn else 1.0
        )

        score = score_neighbor(
            neighbor,
            edge,
            now,
            context_match,
        )

        scored.append((score, neighbor, edge))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:top_k]


def retrieve_subgraph(
    graph: nx.MultiDiGraph,
    seed_nodes: List[str],
    k: int = 2
) -> nx.MultiDiGraph:
    """
    Retrieve a subgraph around seed_nodes up to k-hop neighbors.
    """
    sub_nodes = set()
    for node in seed_nodes:
        neighbors = retrieve_neighbors(graph, node, k=k, top_k=None)
        sub_nodes.add(node)
        sub_nodes.update(neighbors)

    return graph.subgraph(sub_nodes).copy()


def retrieve_path(
    graph: nx.MultiDiGraph,
    start_node: str,
    end_node: str,
    weight: Optional[str] = None
) -> List[List[str]]:
    """
    Retrieve all shortest paths between start_node and end_node.
    If weight is provided, uses weighted shortest path.
    """
    if start_node not in graph or end_node not in graph:
        return []

    try:
        paths = list(nx.all_shortest_paths(graph, source=start_node, target=end_node, weight=weight))
        return paths
    except nx.NetworkXNoPath:
        return []
