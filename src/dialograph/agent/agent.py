from typing import Any, List, Dict
import json

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

# ------------------------------------------------------------------
# Base Agent
# ------------------------------------------------------------------
class Agent:
    def __init__(self):
        self.cost = 0

    def next_action(self, conversation: List[Dict[str, str]]) -> str:
        raise NotImplementedError


# ------------------------------------------------------------------
# Dialograph Agent (LangChain)
# ------------------------------------------------------------------
class DialographAgent(Agent):
    """
    Dialograph-style agent using LangChain.
    Maintains a lightweight graph-based memory.
    """

    def __init__(
        self,
        data_name: str,
        mode: str,
        activate_top_k: int = 5,
        model_name: str = "llama-3.1-8b-instant",
    ):
        super().__init__()
        self.data_name = data_name
        self.mode = mode
        self.activate_top_k = activate_top_k

        self.activated_memory_nodes: List[str] = []
        self.graph_edges: List[Dict[str, Any]] = []

        self.llm = ChatGroq(model=model_name)

        self.system_message = SystemMessage(
            content=(
                f"You are a proactive agent for {self.data_name}. "
                "Be concise, relevant, and memory-aware."
            )
        )

    # ------------------------------------------------------------------
    # Core
    # ------------------------------------------------------------------
    def next_action(self, conversation: List[Dict[str, str]]) -> str:
        self.update_graph_from_conversation(conversation)

        activated_nodes = self.retrieve_nodes(conversation)
        last_message = conversation[-1]["content"] if conversation else "Hello"

        messages = [
            self.system_message,
            HumanMessage(
                content=(
                    f"The user said:\n{last_message}\n\n"
                    f"Memory Nodes:\n{activated_nodes}\n\n"
                    "Generate the next assistant response."
                )
            ),
        ]

        response = self.llm.invoke(messages)
        return response.content

    # ------------------------------------------------------------------
    # Graph Extraction
    # ------------------------------------------------------------------
    def extract_nodes_and_relations(
        self, conversation: List[Dict[str, str]]
    ) -> Dict[str, Any]:

        prompt = (
            "Extract key concepts and relationships from the conversation.\n"
            "Return ONLY valid JSON in this format:\n"
            "{"
            '"nodes": [{"id": "...", "type": "...", "content": "..."}], '
            '"edges": [{"source": "...", "target": "...", "relation_type": "..."}]'
            "}\n\n"
            f"Conversation:\n{conversation}"
        )

        response = self.llm.invoke([HumanMessage(content=prompt)])
        raw = response.content.strip()
        print("RAWWWWWWWWWWWWW: ", raw)

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"nodes": [], "edges": []}

    def update_graph_from_conversation(self, conversation: List[Dict[str, str]]) -> None:
        graph_data = self.extract_nodes_and_relations(conversation)

        print("++++++++++++++++++++++++++++++++++++++++++++++++")
        print("GRAPHS:", graph_data)
        print("++++++++++++++++++++++++++++++++++++++++++++++++")

        for node in graph_data.get("nodes", []):
            node_id = node.get("id")
            if node_id and node_id not in self.activated_memory_nodes:
                self.activated_memory_nodes.append(node_id)

        self.graph_edges.extend(graph_data.get("edges", []))

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------
    def retrieve_nodes(self, conversation: List[Dict[str, str]]) -> List[str]:
        return self.activated_memory_nodes[: self.activate_top_k]

    # ------------------------------------------------------------------
    # Reflection / Learning Hooks
    # ------------------------------------------------------------------
    def revision(self, conversation: List[Dict[str, str]]) -> str:
        prompt = (
            "Review the assistant's last response and suggest improvements.\n\n"
            f"Conversation:\n{conversation}"
        )
        return self.llm.invoke([HumanMessage(content=prompt)]).content

    def extract_from_failure(self, conversation: List[Dict[str, str]]) -> str:
        prompt = (
            "Extract a concise lesson from the failure below.\n\n"
            f"{conversation}"
        )
        return self.llm.invoke([HumanMessage(content=prompt)]).content

    def extract_from_success(self, conversation: List[Dict[str, str]]) -> str:
        prompt = (
            "Extract a concise reusable insight from the success below.\n\n"
            f"{conversation}"
        )
        return self.llm.invoke([HumanMessage(content=prompt)]).content

    def reinterpretation(self, conversation: List[Dict[str, str]]) -> str:
        nodes = self.retrieve_nodes(conversation)
        if not nodes:
            return ""

        prompt = (
            "Using the memory below, give concise guidance for the next response.\n\n"
            f"Memory:\n{nodes}\n\nConversation:\n{conversation}"
        )
        return self.llm.invoke([HumanMessage(content=prompt)]).content

    # ------------------------------------------------------------------
    # Persistence Placeholder
    # ------------------------------------------------------------------
    def save_nodes(self, conversation: List[Dict[str, str]]) -> None:
        self.activated_memory_nodes.append("placeholder_node")
