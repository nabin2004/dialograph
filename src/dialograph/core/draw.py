from pyvis.network import Network
from pathlib import Path
import webbrowser
import http.server
import socketserver
import threading
import socket


def find_free_port(start_port=8000, max_attempts=10):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    raise OSError(f"Could not find a free port in range {start_port}-{start_port + max_attempts}")


def draw(graph, filename="dialograph.html", title="Dialograph Visualization", 
         height="800px", width="100%", node_color="crimson", physics=True,
         serve=False, port=8000):
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
    serve : bool
        Whether to start a local server and open in browser.
    port : int
        Port number for the local server (default: 8000).
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
    
    # Serve and open in browser if requested
    if serve:
        file_path = Path(filename).resolve()
        directory = file_path.parent
        
        # Find an available port if the requested one is in use
        try:
            actual_port = find_free_port(port)
            if actual_port != port:
                print(f"[Dialograph] Port {port} in use, using {actual_port} instead")
        except OSError as e:
            print(f"[Dialograph] Error: {e}")
            return
        
        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(directory), **kwargs)
        
        def start_server():
            with socketserver.TCPServer(("", actual_port), Handler) as httpd:
                print(f"[Dialograph] Serving at http://localhost:{actual_port}")
                httpd.serve_forever()
        
        # Start server in background thread
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        
        # Open browser
        url = f'http://localhost:{actual_port}/{file_path.name}'
        webbrowser.open(url)
        print(f"[Dialograph] Opening browser at {url}")
        print(f"[Dialograph] Press Ctrl+C to stop")
        
        # Keep running
        try:
            while True:
                threading.Event().wait(1)
        except KeyboardInterrupt:
            print("\n[Dialograph] Server stopped")