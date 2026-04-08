from dialograph import Node, Edge, Dialograph, draw

graph = Dialograph()

# Nabin Eats Rice.
n1 = Node(node_id='n1',node_type='personal_details',data={"value":"Prdip"})
n2 = Node(node_id='n2',node_type="object", data={"value":"Rice"})
n3 = Node(node_id='n3',node_type='personal_details',data={"value":"Football"})
n4 = Node(node_id='n4',node_type='person',data={"value":"R. Feynman"})
n5 = Node(node_id='n5',node_type='subject',data={"value":"Quantum Physics"})
n6 = Node(node_id='n6',node_type='subject',data={"value":"Space"})
n7 = Node(node_id='n7',node_type='personal_details',data={"value":"Goth baddie"})
n8 = Node(node_id='n8',node_type='personal_details',data={"value":"Asian baddie"})





e1 = Edge(edge_id='e1', source_node_id='n1', target_node_id='n2', relation='eats')
e2 = Edge(edge_id='e2', source_node_id='n1', target_node_id='n4', relation='knows')
e3 = Edge(edge_id='e3', source_node_id='n1', target_node_id='n3', relation='plays')
e4 = Edge(edge_id='e4', source_node_id='n1', target_node_id='n5', relation='interested')
e5 = Edge(edge_id='e5', source_node_id='n4', target_node_id='n5', relation='famousFor')
e6 = Edge(edge_id='e6', source_node_id='n1', target_node_id='n6', relation='interested')
e7 = Edge(edge_id='e7', source_node_id='n1', target_node_id='n7', relation='interested')
e8 = Edge(edge_id='e8', source_node_id='n1', target_node_id='n8', relation='interested')



graph.add_node(n1)
graph.add_node(n2)
graph.add_node(n3)
graph.add_node(n4)
graph.add_node(n5)
graph.add_node(n6)
graph.add_node(n7)
graph.add_node(n8)

graph.add_edge(e1)
graph.add_edge(e2)
graph.add_edge(e3)
graph.add_edge(e4)
graph.add_edge(e5)
graph.add_edge(e6)
graph.add_edge(e7)
graph.add_edge(e8)

draw(graph, serve=True)