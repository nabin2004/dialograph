from pyvis.network import Network
from pathlib import Path

def draw(graph, filename="dialograph.html", title="Dialograph Visualization", 
         height="800px", width="100%", node_color="crimson", physics=True):
    """
    Render an interactive, browser-based visualization of the Dialograph with pointy edges.

    Parameters
    ----------
    graph : Dialograph
        Your Dialograph object containing nodes and edges.
    filename : str
        Path to save the interactive HTML file.
    title : str
        Title displayed on the HTML page.
    height : str
        Height of the browser canvas (e.g., '800px').
    width : str
        Width of the browser canvas (e.g., '100%').
    node_color : str
        Default color for nodes.
    physics : bool
        Whether to enable physics-based smooth layout.
    """
    net = Network(height=height, width=width, bgcolor="#ffffff", font_color="black", heading=title)

    # Add nodes
    for node_id, node in graph.nodes.items():
        value = node.data.get("value") or node.data.get("text") or str(node.node_id)
        net.add_node(node_id, label=value, shape="box", color=node_color)

    # Add edges with pointy arrows
    for edge_id, edge in graph.edges.items():
        net.add_edge(
            edge.source_node_id,
            edge.target_node_id,
            label=edge.relation,
            color="black",
            arrows="to",
            arrowScale=2.0,       # make it pointy
            arrowStrikethrough=False
        )

    # Physics layout for smooth visualization
    if physics:
        net.barnes_hut(gravity=-20000, spring_length=200, spring_strength=0.05)

    # Ensure directory exists
    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    
    # Save interactive HTML
    net.save_graph(filename)
    print(f"[Dialograph] Interactive visualization saved to: {filename}")
