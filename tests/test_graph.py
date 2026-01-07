import pytest
import os
from dialograph.core.graph import Dialograph


class TestDialographInit:
    """Test Dialograph initialization"""
    
    def test_init_creates_empty_graph(self):
        dg = Dialograph()
        assert len(dg.graph.nodes) == 0
        assert len(dg.graph.edges) == 0
    
    def test_init_sets_time_to_zero(self):
        dg = Dialograph()
        assert dg.time == 0


class TestDialographStep:
    """Test time stepping functionality"""
    
    def test_step_increments_time(self):
        dg = Dialograph()
        assert dg.time == 0
        dg.step()
        assert dg.time == 1
    
    def test_step_returns_new_time(self):
        dg = Dialograph()
        result = dg.step()
        assert result == 1
    
    def test_multiple_steps(self):
        dg = Dialograph()
        for i in range(1, 6):
            result = dg.step()
            assert result == i
            assert dg.time == i


class TestDialographAddNode:
    """Test node addition functionality"""
    
    def test_add_node_basic(self):
        dg = Dialograph()
        dg.add_node("A")
        assert "A" in dg.graph.nodes
    
    def test_add_node_with_attributes(self):
        dg = Dialograph()
        dg.add_node("A", label="Node A", value=10)
        node_data = dg.graph.nodes["A"]
        assert node_data["label"] == "Node A"
        assert node_data["value"] == 10
    
    def test_add_node_includes_created_at_timestamp(self):
        dg = Dialograph()
        dg.time = 5
        dg.add_node("A")
        assert dg.graph.nodes["A"]["created_at"] == 5
    
    def test_add_multiple_nodes(self):
        dg = Dialograph()
        dg.add_node("A")
        dg.add_node("B")
        dg.add_node("C")
        assert len(dg.graph.nodes) == 3


class TestDialographAddEdge:
    """Test edge addition functionality"""
    
    def test_add_edge_basic(self):
        dg = Dialograph()
        dg.add_node("A")
        dg.add_node("B")
        key = dg.add_edge("A", "B")
        assert dg.graph.has_edge("A", "B", key)
    
    def test_add_edge_returns_key(self):
        dg = Dialograph()
        dg.add_node("A")
        dg.add_node("B")
        key = dg.add_edge("A", "B")
        assert key == 0  # First edge gets key 0
    
    def test_add_edge_with_attributes(self):
        dg = Dialograph()
        dg.add_node("A")
        dg.add_node("B")
        key = dg.add_edge("A", "B", weight=5, relation="connects")
        edge_data = dg.graph.edges["A", "B", key]
        assert edge_data["weight"] == 5
        assert edge_data["relation"] == "connects"
    
    def test_add_edge_includes_created_at_timestamp(self):
        dg = Dialograph()
        dg.add_node("A")
        dg.add_node("B")
        dg.time = 3
        key = dg.add_edge("A", "B")
        assert dg.graph.edges["A", "B", key]["created_at"] == 3
    
    def test_add_multiple_edges_between_same_nodes(self):
        """Test MultiDiGraph functionality - multiple edges between same nodes"""
        dg = Dialograph()
        dg.add_node("A")
        dg.add_node("B")
        key1 = dg.add_edge("A", "B", type="type1")
        key2 = dg.add_edge("A", "B", type="type2")
        assert key1 != key2
        assert dg.graph.has_edge("A", "B", key1)
        assert dg.graph.has_edge("A", "B", key2)


class TestDialographUpdateNode:
    """Test node update functionality"""
    
    def test_update_node_basic(self):
        dg = Dialograph()
        dg.add_node("A", value=10)
        dg.step()
        dg.update_node("A", value=20)
        assert dg.graph.nodes["A"]["value"] == 20
    
    def test_update_node_adds_updated_at_timestamp(self):
        dg = Dialograph()
        dg.add_node("A")
        dg.time = 5
        dg.update_node("A", value=20)
        assert dg.graph.nodes["A"]["updated_at"] == 5
    
    def test_update_node_preserves_existing_attributes(self):
        dg = Dialograph()
        dg.add_node("A", label="Node A", value=10)
        dg.update_node("A", value=20)
        assert dg.graph.nodes["A"]["label"] == "Node A"
        assert dg.graph.nodes["A"]["value"] == 20
    
    def test_update_nonexistent_node_raises_error(self):
        dg = Dialograph()
        with pytest.raises(ValueError, match="Node Z does not exist"):
            dg.update_node("Z", value=10)


class TestDialographUpdateEdge:
    """Test edge update functionality"""
    
    def test_update_edge_basic(self):
        dg = Dialograph()
        dg.add_node("A")
        dg.add_node("B")
        key = dg.add_edge("A", "B", weight=5)
        dg.step()
        dg.update_edge("A", "B", key, weight=10)
        assert dg.graph.edges["A", "B", key]["weight"] == 10
    
    def test_update_edge_adds_updated_at_timestamp(self):
        dg = Dialograph()
        dg.add_node("A")
        dg.add_node("B")
        key = dg.add_edge("A", "B")
        dg.time = 7
        dg.update_edge("A", "B", key, weight=10)
        assert dg.graph.edges["A", "B", key]["updated_at"] == 7
    
    def test_update_edge_preserves_existing_attributes(self):
        dg = Dialograph()
        dg.add_node("A")
        dg.add_node("B")
        key = dg.add_edge("A", "B", weight=5, relation="connects")
        dg.update_edge("A", "B", key, weight=10)
        assert dg.graph.edges["A", "B", key]["relation"] == "connects"
        assert dg.graph.edges["A", "B", key]["weight"] == 10
    
    def test_update_nonexistent_edge_raises_error(self):
        dg = Dialograph()
        dg.add_node("A")
        dg.add_node("B")
        with pytest.raises(ValueError, match="Edge .* does not exist"):
            dg.update_edge("A", "B", 0, weight=10)


class TestDialographGetNodeState:
    """Test node state retrieval"""
    
    def test_get_node_state_returns_all_attributes(self):
        dg = Dialograph()
        dg.add_node("A", label="Node A", value=10)
        state = dg.get_node_state("A")
        assert state["label"] == "Node A"
        assert state["value"] == 10
        assert "created_at" in state
    
    def test_get_node_state_returns_dict(self):
        dg = Dialograph()
        dg.add_node("A")
        state = dg.get_node_state("A")
        assert isinstance(state, dict)
    
    def test_get_nonexistent_node_state_raises_error(self):
        dg = Dialograph()
        with pytest.raises(ValueError, match="Node Z does not exist"):
            dg.get_node_state("Z")


class TestDialographGetEdgeState:
    """Test edge state retrieval"""
    
    def test_get_edge_state_returns_all_attributes(self):
        dg = Dialograph()
        dg.add_node("A")
        dg.add_node("B")
        key = dg.add_edge("A", "B", weight=5, relation="connects")
        state = dg.get_edge_state("A", "B", key)
        assert state["weight"] == 5
        assert state["relation"] == "connects"
        assert "created_at" in state
    
    def test_get_edge_state_returns_dict(self):
        dg = Dialograph()
        dg.add_node("A")
        dg.add_node("B")
        key = dg.add_edge("A", "B")
        state = dg.get_edge_state("A", "B", key)
        assert isinstance(state, dict)
    
    def test_get_nonexistent_edge_state_raises_error(self):
        dg = Dialograph()
        dg.add_node("A")
        dg.add_node("B")
        with pytest.raises(ValueError, match="Edge .* does not exist"):
            dg.get_edge_state("A", "B", 0)


class TestDialographSaveLoad:
    """Test save and load functionality"""
    
    def test_save_creates_file(self, tmp_path):
        dg = Dialograph()
        dg.add_node("A")
        filepath = tmp_path / "test_graph.pkl"
        dg.save(str(filepath))
        assert filepath.exists()
    
    def test_load_restores_graph_structure(self, tmp_path):
        # Create and save a graph
        dg1 = Dialograph()
        dg1.add_node("A", label="Node A")
        dg1.add_node("B", label="Node B")
        key = dg1.add_edge("A", "B", weight=5)
        filepath = tmp_path / "test_graph.pkl"
        dg1.save(str(filepath))
        
        # Load into new graph
        dg2 = Dialograph()
        dg2.load(str(filepath))
        
        assert "A" in dg2.graph.nodes
        assert "B" in dg2.graph.nodes
        assert dg2.graph.has_edge("A", "B", key)
        assert dg2.graph.nodes["A"]["label"] == "Node A"
        assert dg2.graph.edges["A", "B", key]["weight"] == 5
    
    def test_load_restores_time_state(self, tmp_path):
        dg1 = Dialograph()
        dg1.step()
        dg1.step()
        dg1.step()
        filepath = tmp_path / "test_graph.pkl"
        dg1.save(str(filepath))
        
        dg2 = Dialograph()
        dg2.load(str(filepath))
        assert dg2.time == 3


class TestDialographIntegration:
    """Integration tests for complete workflows"""
    
    def test_complete_workflow(self):
        """Test a complete workflow with all operations"""
        dg = Dialograph()
        
        # Add nodes
        dg.add_node("A", label="Node A", value=10)
        dg.step()
        dg.add_node("B", label="Node B", value=20)
        dg.step()
        
        # Add edge
        key = dg.add_edge("A", "B", weight=5, relation="connects")
        dg.step()
        
        # Update node
        dg.update_node("A", value=15, status="updated")
        
        # Verify states
        node_state = dg.get_node_state("A")
        assert node_state["value"] == 15
        assert node_state["status"] == "updated"
        assert node_state["created_at"] == 0
        assert node_state["updated_at"] == 3
        
        edge_state = dg.get_edge_state("A", "B", key)
        assert edge_state["weight"] == 5
        assert edge_state["created_at"] == 2
    
    def test_temporal_tracking(self):
        """Test that temporal tracking works correctly"""
        dg = Dialograph()
        
        # Time 0: Create node A
        dg.add_node("A", value=1)
        assert dg.graph.nodes["A"]["created_at"] == 0
        
        # Time 1: Create node B
        dg.step()
        dg.add_node("B", value=2)
        assert dg.graph.nodes["B"]["created_at"] == 1
        
        # Time 2: Update node A
        dg.step()
        dg.update_node("A", value=10)
        assert dg.graph.nodes["A"]["updated_at"] == 2
        
        # Time 3: Add edge
        dg.step()
        key = dg.add_edge("A", "B")
        assert dg.graph.edges["A", "B", key]["created_at"] == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])