# Visualization

Dialograph provides two visualization functions for exploring and debugging your graphs:

- **`draw()`**: Static, deterministic visualization (recommended for most use cases)
- **`draw_live()`**: Interactive visualization with a local server (for exploration and debugging)

## Quick Start

### Static Visualization

```python
from dialograph import Dialograph, Node, Edge, draw

# Create a graph
graph = Dialograph()
n1 = Node(node_id='n1', node_type='person', data={"value": "Alice"})
n2 = Node(node_id='n2', node_type='person', data={"value": "Bob"})
e1 = Edge(edge_id='e1', source_node_id='n1', target_node_id='n2', relation='knows')

graph.add_node(n1)
graph.add_node(n2)
graph.add_edge(e1)

# Generate visualization
html = draw(graph)  # Returns HTML string

# Or save to file
draw(graph, filename="my_graph.html")
```

### Interactive Visualization

```python
from dialograph import Dialograph, Node, Edge, draw_live

# Create a graph (same as above)
graph = Dialograph()
# ... add nodes and edges ...

# Start interactive server
server = draw_live(graph)
# Browser opens automatically at http://127.0.0.1:<port>/

# When done, shut down the server
server.shutdown()

# Or use as a context manager
with draw_live(graph) as server:
    # Interact with graph in browser
    pass  # Server stops automatically when exiting context
```

## `draw()` - Static Visualization

### Overview

The `draw()` function creates a **deterministic, predictable** visualization of your graph. It's designed to be:

- **Consistent**: Same graph always produces the same layout
- **Safe**: No side effects, doesn't mutate your graph
- **Flexible**: Can return HTML or save to a file

### Parameters

```python
draw(
    graph,
    filename=None,           # Optional: save to file
    title="Dialograph Visualization",
    height="800px",
    width="100%",
    node_colors=None,        # Optional: custom color scheme
    edge_colors=None,        # Optional: custom color scheme
    physics=False,           # False for deterministic layout
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `graph` | `Dialograph` | Required | The graph to visualize |
| `filename` | `str` or `None` | `None` | If provided, saves HTML to this path |
| `title` | `str` | `"Dialograph Visualization"` | Page title |
| `height` | `str` | `"800px"` | Canvas height |
| `width` | `str` | `"100%"` | Canvas width |
| `node_colors` | `dict` or `None` | `None` | Color mapping for node types |
| `edge_colors` | `dict` or `None` | `None` | Color mapping for edge relations |
| `physics` | `bool` | `False` | Enable physics-based layout (non-deterministic) |

### Returns

- **`str`**: HTML content of the visualization

### Default Color Schemes

#### Node Colors (by `node_type`)

```python
{
    "personal_details": "#FF6B6B",  # Red
    "object": "#4ECDC4",            # Teal
    "person": "#45B7D1",            # Blue
    "subject": "#FFA07A",           # Light Salmon
    "message": "#98D8C8",           # Mint
    "default": "#95A5A6",           # Gray
}
```

#### Edge Colors (by `relation`)

```python
{
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
```

### Custom Colors

```python
custom_node_colors = {
    "person": "#FF0000",     # Red
    "place": "#00FF00",      # Green
    "default": "#0000FF",    # Blue (fallback)
}

custom_edge_colors = {
    "knows": "#FF00FF",      # Magenta
    "visits": "#00FFFF",     # Cyan
    "default": "#FFFF00",    # Yellow (fallback)
}

html = draw(
    graph,
    node_colors=custom_node_colors,
    edge_colors=custom_edge_colors
)
```

### Edge Cases

The `draw()` function handles these edge cases gracefully:

#### Empty Graph

```python
empty_graph = Dialograph()
html = draw(empty_graph)
# Displays: "Empty Graph" placeholder
```

#### Single Node

```python
graph = Dialograph()
graph.add_node(Node(node_id='n1', node_type='test', data={"value": "Lonely"}))
html = draw(graph)
# Displays: Single node without errors
```

#### Disconnected Components

```python
# Component 1: Alice → Bob
# Component 2: Charlie → Dave (disconnected from component 1)
html = draw(graph)
# Both components are displayed correctly
```

### Determinism

By default, `draw()` uses a **hierarchical layout** with physics disabled. This ensures that:

- The same graph always produces the same visual layout
- Output is predictable and reproducible
- Ideal for documentation, reports, and demos

```python
# These will produce identical output
html1 = draw(graph, physics=False)
html2 = draw(graph, physics=False)
assert html1 == html2  # True
```

To enable a dynamic, physics-based layout (non-deterministic):

```python
html = draw(graph, physics=True)
```

### Examples

#### Basic Usage

```python
from dialograph import Dialograph, Node, Edge, draw

graph = Dialograph()

# Add nodes
graph.add_node(Node(node_id='n1', node_type='person', data={"value": "Alice"}))
graph.add_node(Node(node_id='n2', node_type='person', data={"value": "Bob"}))

# Add edge
graph.add_edge(Edge(edge_id='e1', source_node_id='n1', target_node_id='n2', relation='knows'))

# Get HTML
html = draw(graph)
print(html)  # Full HTML content
```

#### Save to File

```python
# Save to specific location
draw(graph, filename="output/graph.html")

# Open in browser
import webbrowser
webbrowser.open("output/graph.html")
```

#### Custom Styling

```python
# Custom colors
node_colors = {
    "person": "#FF5733",
    "place": "#33FF57",
}

edge_colors = {
    "knows": "#3357FF",
    "visits": "#FF33A1",
}

html = draw(
    graph,
    title="My Custom Graph",
    height="1000px",
    node_colors=node_colors,
    edge_colors=edge_colors,
    physics=True  # Enable physics for dynamic layout
)
```

---

## `draw_live()` - Interactive Visualization

### Overview

The `draw_live()` function starts a **local HTTP server** for interactive graph exploration. It's designed for:

- **Interactive exploration**: Zoom, pan, drag nodes
- **Debugging**: Hover to inspect node/edge metadata
- **Development**: Quick visual feedback during development

**Important constraints:**

- Runs only on localhost (no external access)
- Ephemeral (no persistent state)
- Lightweight (no heavy dependencies)

### Parameters

```python
draw_live(
    graph,
    host="127.0.0.1",       # Localhost only
    port=0,                 # Auto-assign free port
    open_browser=True,      # Auto-open in browser
    title="Dialograph Live Visualization",
    height="800px",
    width="100%",
    node_colors=None,
    edge_colors=None,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `graph` | `Dialograph` | Required | The graph to visualize |
| `host` | `str` | `"127.0.0.1"` | Server host (localhost) |
| `port` | `int` | `0` | Server port (0 = auto-assign) |
| `open_browser` | `bool` | `True` | Auto-open browser window |
| `title` | `str` | `"Dialograph Live Visualization"` | Page title |
| `height` | `str` | `"800px"` | Canvas height |
| `width` | `str` | `"100%"` | Canvas width |
| `node_colors` | `dict` or `None` | `None` | Custom node colors |
| `edge_colors` | `dict` or `None` | `None` | Custom edge colors |

### Returns

- **`LiveVisualizationServer`**: Server instance with methods:
  - `shutdown()`: Stop the server
  - `is_running()`: Check server status
  - `url`: Server URL (e.g., `"http://127.0.0.1:8080/"`)

### Examples

#### Basic Usage

```python
from dialograph import Dialograph, Node, Edge, draw_live

graph = Dialograph()
# ... add nodes and edges ...

# Start server (browser opens automatically)
server = draw_live(graph)

# Interact with graph in browser...

# When done, shut down
server.shutdown()
```

#### Custom Port

```python
# Use a specific port
server = draw_live(graph, port=8080)
print(server.url)  # http://127.0.0.1:8080/
server.shutdown()
```

#### Without Auto-Open Browser

```python
# Don't open browser automatically
server = draw_live(graph, open_browser=False)
print(f"Visit: {server.url}")
# Manually open in browser later
server.shutdown()
```

#### Context Manager Pattern

```python
# Automatically shutdown when done
with draw_live(graph) as server:
    print(f"Server running at: {server.url}")
    # Interact with graph...
    # Do other work...
# Server stops automatically
```

#### Multiple Graphs

```python
# Run multiple servers simultaneously
graph1 = Dialograph()
# ... add nodes to graph1 ...

graph2 = Dialograph()
# ... add nodes to graph2 ...

server1 = draw_live(graph1, port=0)  # Auto-assign port
server2 = draw_live(graph2, port=0)  # Auto-assign different port

print(f"Graph 1: {server1.url}")
print(f"Graph 2: {server2.url}")

# Shut down both
server1.shutdown()
server2.shutdown()
```

### Interactive Features

When you open the live visualization in a browser, you can:

1. **Zoom**: Use mouse wheel or trackpad
2. **Pan**: Click and drag the background
3. **Move nodes**: Click and drag individual nodes (when physics enabled)
4. **Hover**: Hover over nodes/edges to see metadata
5. **Inspect**: See node types, edge relations, and IDs

### Clean Shutdown

Always shut down the server when done:

```python
# Method 1: Manual shutdown
server = draw_live(graph)
# ... do work ...
server.shutdown()

# Method 2: Context manager (automatic)
with draw_live(graph) as server:
    # ... do work ...
    pass  # Automatically shuts down

# Method 3: Check if running
server = draw_live(graph)
if server.is_running():
    print("Server is running")
server.shutdown()
```

---

## Comparison: `draw()` vs `draw_live()`

| Feature | `draw()` | `draw_live()` |
|---------|----------|---------------|
| **Output** | HTML string | HTTP server |
| **Deterministic** | ✅ Yes (physics=False) | ❌ No (physics enabled) |
| **Interactive** | ❌ No | ✅ Yes (zoom, pan, hover) |
| **Side effects** | None | Starts server |
| **Use case** | Reports, docs, static | Debugging, exploration |
| **Physics** | Disabled by default | Enabled by default |
| **Shutdown needed** | ❌ No | ✅ Yes |

---

## Best Practices

### When to Use `draw()`

✅ Use `draw()` when:

- Creating documentation or reports
- Generating visualizations for version control
- You need consistent, reproducible output
- You want to embed HTML in other applications
- No interactivity is required

### When to Use `draw_live()`

✅ Use `draw_live()` when:

- Debugging graph structure during development
- Exploring large or complex graphs interactively
- Demonstrating graph evolution in real-time
- You need to inspect node/edge metadata on hover

### General Guidelines

1. **Always shut down servers**: Use `server.shutdown()` or context managers
2. **Don't commit HTML files**: Generated visualizations are build artifacts
3. **Use custom colors**: For better visual distinction of node/edge types
4. **Handle empty graphs**: Both functions handle this gracefully
5. **No mutations**: Neither function modifies your graph

---

## Troubleshooting

### Port Already in Use

If you get a "port already in use" error with `draw_live()`:

```python
# Let the system auto-assign a free port
server = draw_live(graph, port=0)  # port=0 means auto-assign
```

### Browser Doesn't Open

If the browser doesn't open automatically:

```python
server = draw_live(graph, open_browser=False)
print(f"Manually visit: {server.url}")
```

### Server Won't Stop

If the server doesn't stop cleanly:

```python
# Force shutdown
server.shutdown()

# Or use context manager for automatic cleanup
with draw_live(graph) as server:
    pass  # Auto-stops on exit
```

### Empty Visualization

If the visualization is empty:

```python
# Check if graph has nodes
print(f"Nodes: {len(graph.nodes)}")
print(f"Edges: {len(graph.edges)}")

# Empty graphs show "Empty Graph" message
```

---

## API Reference

For complete API documentation, see:

- [`draw()` API Reference](api/draw.md)
- [`draw_live()` API Reference](api/draw_live.md)
- [Dialograph Core API](api/dialograph.md)
