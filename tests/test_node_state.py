# import time
# import math
# import pytest

# from dialograph import Node


# def test_initial_forgetting_score():
#     node = Node(node_id=1, node_type="belief", confidence=1.0)
#     assert node.forgetting_score == 0.0


# def test_decay_reduces_confidence_and_increases_forgetting():
#     node = Node(node_id=1, node_type="belief", confidence=1.0)

#     # simulate time passing
#     time.sleep(0.05)

#     old_confidence = node.confidence
#     old_forgetting = node.forgetting_score

#     node.decay(decay_rate_per_second=0.1)

#     assert node.confidence < old_confidence
#     assert node.forgetting_score > old_forgetting
#     assert 0.0 < node.confidence <= 1.0
#     assert 0.0 <= node.forgetting_score < 1.0


# def test_forgetting_score_matches_confidence():
#     node = Node(node_type="belief", confidence=0.75)
#     assert math.isclose(node.forgetting_score, 0.25, rel_tol=1e-6)


# def test_persistent_node_never_decays():
#     node = Node(
#         node_type="core-strategy",
#         confidence=1.0,
#         persistent=True,
#     )

#     time.sleep(0.1)
#     node.decay(decay_rate_per_second=1.0)

#     assert node.confidence == 1.0
#     assert node.forgetting_score == math.inf


# def test_multiple_decays_accumulate():
#     node = Node(node_type="belief", confidence=1.0)

#     time.sleep(0.05)
#     node.decay(decay_rate_per_second=0.1)
#     first_confidence = node.confidence

#     time.sleep(0.05)
#     node.decay(decay_rate_per_second=0.1)

#     assert node.confidence < first_confidence
#     assert node.forgetting_score > 0.0


# def test_confidence_clamped_for_forgetting_score():
#     node = Node(node_type="belief", confidence=2.0)
#     assert node.forgetting_score == 0.0

#     node.confidence = -1.0
#     node.forgetting_score = node._compute_forgetting_score()
#     assert node.forgetting_score == 1.0
