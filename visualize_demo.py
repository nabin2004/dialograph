from dialograph import Dialograph, Node, Edge, draw

def main():
    # 1. Create graph
    print("📊 Creating graph...")
    g = Dialograph()
    
    # 2. Add some nodes
    print("📝 Adding nodes...")
    n1 = Node(node_id="A", node_type="concept", data={"value": "Concept A"})
    n2 = Node(node_id="B", node_type="concept", data={"value": "Concept B"})
    g.add_node(n1)
    g.add_node(n2)
    
    # 3. Add an edge
    print("🔗 Adding edge...")
    e1 = Edge(edge_id="e1", source_node_id="A", target_node_id="B", relation="leads_to", strength=0.5)
    g.add_edge(e1)
    
    # 4. Visualize
    print("🎨 Generating visualization...")
    draw(g, filename="demo_visualization.html", title="Demo Visualization")
    print("✅ Done! Open demo_visualization.html in your browser.")

if __name__ == "__main__":
    main()
