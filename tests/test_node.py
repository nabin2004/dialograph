import math
import time
import pytest

from dialograph import Node

def test_node_initialization_defaults():
    node = Node(node_id="n1", node_type="personal_detail", data={"name": "Nabin"}, persistent=True)

    assert node.node_id == "n1"
    assert node.node_type == "personal_detail"
    assert node.data == {"name": "Nabin"}
    assert node.confidence == 1.0
    assert node.persistent is True
    assert isinstance(node.created_at, float)
    assert isinstance(node.last_accessed, float)


@pytest.mark.parametrize(
    "confidence, expected",
    [
        (1.0, 0.0),
        (0.8, 0.2),
        (0.0, 1.0),
        (-1.0, 1.0),   # clamped
        (2.0, 0.0),    # clamped
    ],
)
def test_forgetting_score_clamping(confidence, expected):
    node = Node(
        node_id="n1",
        node_type="message",
        confidence=confidence,
    )

    assert node.forgetting_score == pytest.approx(expected)

def test_persistent_node_never_decays():
    node = Node(
        node_id="n1",
        node_type="message",
        confidence=0.5,
        persistent=True,
    )

    original_confidence = node.confidence
    original_last_accessed = node.last_accessed

    time.sleep(0.01)
    updated_confidence = node.decay()

    assert updated_confidence == original_confidence
    assert node.last_accessed == original_last_accessed
    assert node.forgetting_score == math.inf

def test_confidence_decays_over_time():
    node = Node(
        node_id="n1",
        node_type="message",
        confidence=1.0,
    )

    time.sleep(0.01)
    new_confidence = node.decay(decay_rate_per_second=0.01)

    assert new_confidence < 1.0
    assert node.confidence == new_confidence
    assert node.last_accessed > node.created_at

def test_forgetting_score_updates_after_decay():
    node = Node(
        node_id="n1",
        node_type="message",
        confidence=1.0,
    )

    time.sleep(0.01)
    node.decay(decay_rate_per_second=0.05)

    expected_forgetting = 1.0 - node.confidence
    assert node.forgetting_score == pytest.approx(expected_forgetting)

def test_decay_with_no_elapsed_time_changes_nothing():
    node = Node(
        node_id="n1",
        node_type="message",
        confidence=0.9,
    )

    node.last_accessed = time.time()
    confidence_before = node.confidence

    node.decay(decay_rate_per_second=0.1)

    assert node.confidence == pytest.approx(confidence_before)

def test_string_representation():
    node = Node(
        node_id="n1",
        node_type="message",
        confidence=0.5,
        persistent=False,
    )

    s = str(node)

    assert "Node(" in s
    assert "node_id=n1" in s
    assert "type=message" in s
    assert "confidence=" in s
    assert "forgetting_score=" in s
