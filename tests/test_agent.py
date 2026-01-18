## Check DialographAgent basic functionality

from dialograph import DialographAgent

def main():
    agent = DialographAgent(
        data_name="pg4",
        api_key="",   # empty: Groq is env-based
        mode="train",
        activate_top_k=12,
    )

    conversation = [
        {"role": "user", "content": "Hello"},
        {"role": "user", "content": "What is 2 + 2?"}
    ]

    response = agent.next_action(conversation)

    print("Agent response:")
    print(response)

    # basic sanity checks
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0

    print("Agent check passed")

