from pyvis.network import Network
from pathlib import Path
import tempfile
import http.server
import socketserver
import threading
import webbrowser
import socket
from typing import Optional, Dict


# Color scheme for different node types
DEFAULT_NODE_COLORS = {
    "personal_details": "#FF6B6B",  # Red
    "object": "#4ECDC4",  # Teal
    "person": "#45B7D1",  # Blue
    "subject": "#FFA07A",  # Light Salmon
    "message": "#98D8C8",  # Mint
    "default": "#95A5A6",  # Gray
}

# Color scheme for different edge relations
DEFAULT_EDGE_COLORS = {
    "eats": "#E74C3C",
    "knows": "#3498DB",
    "plays": "#2ECC71",
    "interested": "#F39C12",
    "famousFor": "#9B59B6",
    "supports": "#1ABC9C",
    "contradicts": "#E67E22",
    "elicits": "#16A085",
    "default": "#34495E",
}


def draw(
    graph,
    filename: Optional[str] = None,
    title: str = "Dialograph Visualization",
    height: str = "800px",
    width: str = "100%",
    node_colors: Optional[Dict[str, str]] = None,
    edge_colors: Optional[Dict[str, str]] = None,
    physics: bool = False,
) -> str:
    """
    Render a static, deterministic visualization of the Dialograph.

    This function produces a consistent, predictable visualization for the same graph.
    By default, physics is disabled for deterministic layouts. The visualization
    handles edge cases gracefully (empty graphs, single nodes, disconnected components).

    Parameters
    ----------
    graph : Dialograph
        Your Dialograph object containing nodes and edges.
    filename : str, optional
        Path to save the interactive HTML file. If None, returns HTML as string.
    title : str
        Title displayed on the HTML page.
    height : str
        Height of the browser canvas (e.g., '800px').
    width : str
        Width of the browser canvas (e.g., '100%').
    node_colors : dict, optional
        Color mapping for node types. Uses DEFAULT_NODE_COLORS if not provided.
    edge_colors : dict, optional
        Color mapping for edge relations. Uses DEFAULT_EDGE_COLORS if not provided.
    physics : bool
        Whether to enable physics-based layout. Default is False for deterministic output.

    Returns
    -------
    str
        HTML content of the visualization.

    Examples
    --------
    >>> graph = Dialograph()
    >>> # ... add nodes and edges ...
    >>> html = draw(graph)  # Returns HTML string
    >>> draw(graph, filename="graph.html")  # Saves to file
    """
    # Use default color schemes if not provided
    if node_colors is None:
        node_colors = DEFAULT_NODE_COLORS
    if edge_colors is None:
        edge_colors = DEFAULT_EDGE_COLORS

    net = Network(
        height=height,
        width=width,
        bgcolor="#ffffff",
        font_color="black",
        heading=title,
        directed=True,
    )

    # Handle empty graph
    if not graph.nodes:
        # Create a placeholder message for empty graphs
        net.add_node(
            "empty",
            label="Empty Graph",
            shape="box",
            color="#95A5A6",
            font={"size": 20},
        )
        if filename:
            Path(filename).parent.mkdir(parents=True, exist_ok=True)
            net.save_graph(filename)
            return Path(filename).read_text()
        else:
            # Generate HTML without saving
            return net.generate_html()

    # Add nodes with color by node_type
    for node_id, node in sorted(graph.nodes.items()):  # Sort for determinism
        value = node.data.get("value") or node.data.get("text") or str(node.node_id)
        node_type = getattr(node, "node_type", "default")
        color = node_colors.get(node_type, node_colors.get("default", "#95A5A6"))

        net.add_node(
            node_id,
            label=value,
            shape="box",
            color=color,
            title=f"Type: {node_type}\nID: {node_id}",  # Hover info
        )

    # Add edges with style by relation
    for edge_id, edge in sorted(graph.edges.items()):  # Sort for determinism
        relation = getattr(edge, "relation", "default")
        color = edge_colors.get(relation, edge_colors.get("default", "#34495E"))

        net.add_edge(
            edge.source_node_id,
            edge.target_node_id,
            label=relation,
            color=color,
            arrows="to",
            arrowStrikethrough=False,
            title=f"Relation: {relation}\nID: {edge_id}",  # Hover info
        )

    # Configure layout
    if not physics:
        # Hierarchical layout for determinism
        net.set_options(
            """
        {
            "layout": {
                "hierarchical": {
                    "enabled": true,
                    "levelSeparation": 150,
                    "nodeSpacing": 200,
                    "treeSpacing": 200,
                    "direction": "UD",
                    "sortMethod": "directed"
                }
            },
            "physics": {
                "enabled": false
            },
            "edges": {
                "smooth": {
                    "enabled": true,
                    "type": "cubicBezier"
                }
            }
        }
        """
        )
    else:
        # Physics-based layout for interactive exploration
        net.barnes_hut(gravity=-20000, spring_length=200, spring_strength=0.05)

    # Save or return HTML
    if filename:
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        net.save_graph(filename)
        return Path(filename).read_text()
    else:
        return net.generate_html()


def draw_live(
    graph,
    host: str = "127.0.0.1",
    port: int = 0,
    open_browser: bool = True,
    title: str = "Dialograph Live Visualization",
    height: str = "800px",
    width: str = "100%",
    node_colors: Optional[Dict[str, str]] = None,
    edge_colors: Optional[Dict[str, str]] = None,
) -> "LiveVisualizationServer":
    """
    Start an interactive, local visualization server for graph exploration.

    This function starts a lightweight HTTP server on localhost and opens a browser
    window for interactive graph visualization. The server supports zoom, pan,
    and hover-to-inspect features. It shuts down cleanly on process exit or interrupt.

    Parameters
    ----------
    graph : Dialograph
        Your Dialograph object containing nodes and edges.
    host : str
        Host address to bind the server. Default is "127.0.0.1" (localhost).
    port : int
        Port number for the server. Default is 0 (auto-pick free port).
    open_browser : bool
        Whether to automatically open a browser window. Default is True.
    title : str
        Title displayed on the HTML page.
    height : str
        Height of the browser canvas (e.g., '800px').
    width : str
        Width of the browser canvas (e.g., '100%').
    node_colors : dict, optional
        Color mapping for node types.
    edge_colors : dict, optional
        Color mapping for edge relations.

    Returns
    -------
    LiveVisualizationServer
        Server instance that can be stopped with .shutdown() method.

    Examples
    --------
    >>> graph = Dialograph()
    >>> # ... add nodes and edges ...
    >>> server = draw_live(graph)
    >>> # Interact with graph in browser
    >>> server.shutdown()  # Clean shutdown

    Notes
    -----
    - The server runs in a separate thread and does not block
    - No external cloud dependencies
    - No persistent state unless explicitly enabled
    - Gracefully handles missing dependencies
    """
    # Generate HTML with physics enabled for interactive exploration
    html_content = draw(
        graph,
        filename=None,
        title=title,
        height=height,
        width=width,
        node_colors=node_colors,
        edge_colors=edge_colors,
        physics=True,  # Enable physics for interactive mode
    )

    # Create temporary directory for serving (will be cleaned up on shutdown)
    temp_dir = tempfile.mkdtemp(prefix="dialograph_")

    # Create a socket and bind to find a free port
    # This approach reduces (but doesn't eliminate) the race condition
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        if port == 0:
            sock.bind((host, 0))
            port = sock.getsockname()[1]
        sock.close()
    except OSError:
        sock.close()
        raise

    # Create HTTP server
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, msg_format, *args):
            # Suppress server logs (renamed from 'format' to avoid shadowing builtin)
            pass

        def do_GET(self):
            if self.path == "/" or self.path == "/visualization.html":
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(html_content.encode())
            else:
                self.send_error(404)

    # Try to create server with retry logic for port conflicts
    max_retries = 3
    for attempt in range(max_retries):
        try:
            server = socketserver.TCPServer((host, port), QuietHandler)
            break
        except OSError as e:
            if attempt < max_retries - 1 and port != 0:
                # If specific port is requested and fails, don't retry
                raise
            elif attempt < max_retries - 1:
                # Auto-assigned port failed, try again
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind((host, 0))
                    port = s.getsockname()[1]
            else:
                raise

    server_url = f"http://{host}:{port}/"

    # Start server in background thread
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    print(f"[Dialograph] Live visualization server started at: {server_url}")

    # Open browser if requested
    if open_browser:
        webbrowser.open(server_url)

    # Return server wrapper for clean shutdown
    return LiveVisualizationServer(server, server_url, temp_dir)


class LiveVisualizationServer:
    """
    Wrapper for the live visualization HTTP server.

    Provides methods for clean shutdown and server status.
    """

    def __init__(self, server, url: str, temp_dir: str):
        self.server = server
        self.url = url
        self.temp_dir = temp_dir
        self._running = True

    def shutdown(self):
        """Stop the visualization server and clean up resources."""
        if self._running:
            self.server.shutdown()
            self.server.server_close()
            self._running = False
            
            # Clean up temporary directory
            import shutil
            try:
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            except Exception:
                pass  # Ignore cleanup errors
            
            print(f"[Dialograph] Live visualization server stopped.")

    def is_running(self) -> bool:
        """Check if the server is still running."""
        return self._running

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()

    def __repr__(self):
        status = "running" if self._running else "stopped"
        return f"LiveVisualizationServer(url='{self.url}', status='{status}')"
