import networkx as nx
from typing import List, Optional


def retrieve_neighbors(
    graph: nx.MultiDiGraph,
    node_id: str,
    k: int = 3,
    top_k: int = 5
) -> List[str]:
    """
    Retrieve and rank k-hop neighbors from the graph based on relevance_score.
    """
    if node_id is None:
        return []

    # Get all nodes within k hops
    neighbors = nx.single_source_shortest_path_length(graph, node_id, cutoff=k)
    neighbors.pop(node_id, None)  # remove self

    # Rank neighbors by relevance_score (default 0)
    ranked = sorted(
        neighbors.keys(),
        key=lambda n: graph.nodes[n].get("relevance_score", 0),
        reverse=True
    )

    return ranked[:top_k]


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


def retrieve_strategies(
    graph: nx.MultiDiGraph,
    activated_nodes: List[str],
    conversation: Optional[List[dict]] = None,
    top_k: int = 3
) -> List[str]:
    """
    Retrieve memory strategies (nodes) to guide next actions.
    Strategy nodes are ranked by recency and relevance.
    """
    if not activated_nodes:
        return []

    # prioritize nodes that match keywords in the last user message
    keywords = set()
    if conversation:
        last_msg = conversation[-1]["content"] if conversation else ""
        keywords = set(last_msg.lower().split())

    scored_nodes = []
    for node in activated_nodes:
        node_data = graph.nodes.get(node, {})
        score = node_data.get("relevance_score", 0)
        # small boost if keyword appears in node label
        label = node_data.get("label", "").lower()
        if any(word in label for word in keywords):
            score += 1
        scored_nodes.append((node, score))

    # Rank nodes by score descending
    scored_nodes.sort(key=lambda x: x[1], reverse=True)

    return [node for node, _ in scored_nodes[:top_k]]
