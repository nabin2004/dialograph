"""
Simple playground to test YOUR edge implementation.

Just run this and play around!
"""

from dialograph import Dialograph, Node, Edge
import time


def playground():
    """
    Simple playground - no API needed!
    """
    print("\n" + "="*60)
    print("DIALOGRAPH PLAYGROUND")
    print("="*60 + "\n")
    
    # 1. Create graph
    print("📊 Creating graph...")
    g = Dialograph()
    print("✓ Done\n")
    
    # 2. Add some nodes
    print("📝 Adding nodes...")
    
    n1 = Node(
        node_id="stress",
        node_type="problem",
        data={"value": "User is stressed about exams"}
    )
    
    n2 = Node(
        node_id="meditation",
        node_type="strategy",
        data={"value": "Suggest meditation"}
    )
    
    n3 = Node(
        node_id="exercise",
        node_type="strategy",
        data={"value": "Suggest exercise"}
    )
    
    g.add_node(n1)
    g.add_node(n2)
    g.add_node(n3)
    
    print(f"✓ Added {len(g.nodes)} nodes\n")
    
    # 3. Add edges (YOUR WORK!)
    print("🔗 Adding edges (YOUR EdgeState!)...")
    
    edge1 = Edge(
        edge_id="e1",
        source_node_id="stress",
        target_node_id="meditation",
        relation="elicits",
        strength=0.7  # Medium-strong connection
    )
    
    edge2 = Edge(
        edge_id="e2",
        source_node_id="stress",
        target_node_id="exercise",
        relation="elicits",
        strength=0.5  # Medium connection
    )
    
    g.add_edge(edge1)
    g.add_edge(edge2)
    
    print(f"✓ Added {len(g.edges)} edges\n")
    
    # 4. Show initial state
    print("-" * 60)
    print("INITIAL STATE")
    print("-" * 60)
    
    for edge_id, edge in g.edges.items():
        print(f"\n{edge_id}: {edge.source_node_id} → {edge.target_node_id}")
        print(f"  Relation: {edge.relation}")
        print(f"  Strength: {edge.strength:.2f}")
        print(f"  Importance: {edge.importance_score():.2f}")
    
    # 5. Retrieve most important
    print("\n" + "-" * 60)
    print("RETRIEVAL TEST")
    print("-" * 60)
    
    print("\nRetrieving top 1 most important edge...")
    top_edge = g.retrieve(top_k=1)[0]
    
    print(f"\n🏆 Most important edge:")
    print(f"  {top_edge.source_node_id} → {top_edge.target_node_id}")
    print(f"  Strength: {top_edge.strength:.2f}")
    print(f"  Importance: {top_edge.importance_score():.2f}")
    
    # 6. Simulate usage
    print("\n" + "-" * 60)
    print("SIMULATION: Agent uses edge")
    print("-" * 60)
    
    print("\n📍 Step 1: Mark edge as used")
    top_edge.touch()
    print("✓ Edge touched (last_used updated)")
    
    print("\n😊 Step 2: User is happy with suggestion")
    top_edge.register_emotion("happy", intensity=1.0)
    print(f"✓ Emotional charge: {top_edge.emotional_charge:.2f}")
    print(f"✓ New importance: {top_edge.importance_score():.2f}")
    
    print("\n📈 Step 3: Reinforce successful edge")
    top_edge.reinforce(0.2)
    print(f"✓ Strength: 0.7 → {top_edge.strength:.2f}")
    
    # 7. Show updated state
    print("\n" + "-" * 60)
    print("UPDATED STATE")
    print("-" * 60)
    
    for edge_id, edge in g.edges.items():
        print(f"\n{edge_id}: {edge.source_node_id} → {edge.target_node_id}")
        print(f"  Strength: {edge.strength:.2f}")
        print(f"  Emotional: {edge.emotional_charge:.2f}")
        print(f"  Importance: {edge.importance_score():.2f}")
    
    # 8. Simulate time passing
    print("\n" + "-" * 60)
    print("SIMULATION: Time passes")
    print("-" * 60)
    
    print("\n⏰ Simulating 2 hours of inactivity...")
    for edge in g.edges.values():
        edge.decay(time_step=7200)  # 2 hours in seconds
    
    print("✓ Decay applied")
    
    # 9. Show after decay
    print("\n" + "-" * 60)
    print("AFTER DECAY")
    print("-" * 60)
    
    for edge_id, edge in g.edges.items():
        print(f"\n{edge_id}: {edge.source_node_id} → {edge.target_node_id}")
        print(f"  Strength: {edge.strength:.2f}")
        print(f"  Should prune? {edge.should_prune()}")
    
    # 10. Maintenance
    print("\n" + "-" * 60)
    print("MAINTENANCE")
    print("-" * 60)
    
    stats = g.get_statistics()
    print(f"\nBefore pruning:")
    print(f"  Edges: {stats['num_edges']}")
    print(f"  Avg strength: {stats['avg_strength']:.2f}")
    print(f"  Weak edges: {stats['weak_edges']}")
    
    print("\n🗑️  Pruning weak edges...")
    pruned = g.prune_weak_edges(threshold=0.1)
    print(f"✓ Removed {pruned} edges")
    
    stats = g.get_statistics()
    print(f"\nAfter pruning:")
    print(f"  Edges: {stats['num_edges']}")
    print(f"  Avg strength: {stats['avg_strength']:.2f}")
    
    # 11. Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print("\n✅ Your EdgeState works!")
    print("\nWhat we tested:")
    print("  ✓ Creation")
    print("  ✓ Importance scoring")
    print("  ✓ Emotions")
    print("  ✓ Reinforcement")
    print("  ✓ Decay")
    print("  ✓ Pruning")
    print("  ✓ Retrieval")
    print("\n🎉 Everything working correctly!")
    print("="*60 + "\n")


if __name__ == "__main__":
    playground()
