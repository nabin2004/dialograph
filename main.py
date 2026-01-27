from dialograph import DialographAgent

# Step 1: create the agent
agent = DialographAgent(
    data_name="Personal Assistant",
    mode="chat",
)
conversation = []

def user(text: str):
    conversation.append({"role": "user", "content": text})
    reply = agent.next_action(conversation)
    conversation.append({"role": "assistant", "content": reply})
    print("Assistant:", reply)


user("My name is Nabin Oli.")
# user("I am studying BSc hons computer and Data science.")
# user("How can you help me?")
