from typing import Any, List, Dict
from pydantic_ai import Agent as PydanticAgent
from pydantic_ai.models.groq import GroqModel


class Agent:
    """Base Agent class providing structure and memory placeholders."""
    def __init__(self):
        self.cost = 0

    def next_action(self, conversation: List[Dict[str, str]]) -> str:
        """Subclasses should implement this to generate the next agent action."""
        raise NotImplementedError("Subclasses must implement this method.")


class DialographAgent(Agent):
    """
    Dialograph agent using pydantic_ai for response generation.
    Supports graph memory + temporal context placeholders.
    """
    def __init__(
        self,
        data_name: str,
        api_key: str,
        mode: str,
        activate_top_k: int = 5,
        model_name: str = "llama-3.3-70b-versatile",
    ):
        super().__init__()

        self.data_name = data_name
        self.api_key = api_key
        self.mode = mode
        self.activate_top_k = activate_top_k

        self.activated_memory_nodes: List[str] = []
        self.recontextualized_guidance: List[str] = []

        # Initialize pydantic AI model
        self.model = GroqModel(model_name)
        self.agent = PydanticAgent(
            self.model,
            system_prompt=f"You are a proactive agent for {self.data_name}."
        )

    def next_action(self, conversation: List[Dict[str, str]]) -> str:
        """
        Generate next response using pydantic AI agent.
        Takes the last user message in conversation as input.
        """

        # Step 1: Extract/update memory
        self.update_graph_from_conversation(conversation)

        # Step 2: Retrieve relevant nodes
        activated_nodes = self.retrieve_nodes(conversation)

        # Step 3: Generate response using memory context
        last_message = conversation[-1]["content"] if conversation else "Hello"

        prompt = f"""
        The learner just said:
        {last_message}

        Memory Nodes (activated / relevant):
        {activated_nodes}

        Generate the next assistant response based on memory context.
        """

        response = self.agent.run_sync(prompt)
        return response

    def extract_nodes_and_relations(
        self,
        conversation: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        last_message = conversation[-1]["content"] if conversation else ""
        prompt = f"""
        You are an AI assistant that reads a conversation and outputs:
        1. Key concepts mentioned.
        2. Entities (people, objects, domains).
        3. Strategies or actions implied.
        4. Relations between nodes: 
           - prerequisite_for (concept -> concept)
           - elicited_by (concept -> strategy)
           - related_to (concept -> concept)
        
        Output strictly as JSON with fields:
        nodes: list of {{id, type, content}}
        edges: list of {{source, target, relation_type}}
        
        Conversation:
        {conversation}
        
        Respond only with valid JSON.
        """

        result = self.agent.run_sync(prompt)
        try:
            import json
            graph_data = json.loads(result)
            return graph_data
        except Exception:
            # fallback in case LLM response is malformed
            return {"nodes": [], "edges": []}

    def update_graph_from_conversation(self, conversation: List[Dict[str, str]]):
        """
        Extract nodes and edges from conversation and save them to memory.
        """
        graph_data = self.extract_nodes_and_relations(conversation)
        for node in graph_data.get("nodes", []):
            if node["id"] not in self.activated_memory_nodes:
                self.activated_memory_nodes.append(node["id"])
                # Here we can also save node content/type/reinforcement/etc

        # For edges, we could maintain a separate list or integrate with networkx
        self.graph_edges = getattr(self, "graph_edges", []) + graph_data.get("edges", [])

    def revision(self, conversation: List[Dict[str, str]]) -> str:
        prompt = (
            "Review the assistant's last response and suggest improvements "
            "or corrections if any. Be concise.\n\n"
            f"Conversation:\n{conversation}"
        )
        result = self.agent.run_sync(prompt)
        return result


    def extract_from_failure(self, conversation: List[Dict[str, str]]) -> str:
        prompt = (
            "The agent failed in the following conversation. "
            "Extract a concise lesson that should be remembered to avoid repeating the mistake.\n\n"
            f"{conversation}"
        )
        return self.agent.run_sync(prompt)

    def extract_from_success(self, conversation: List[Dict[str, str]]) -> str:
        prompt = (
            "The agent succeeded in the following interaction. "
            "Extract a concise reusable insight worth remembering.\n\n"
            f"{conversation}"
        )
        return self.agent.run_sync(prompt)


    def retrieve_nodes(self, conversation: List[Dict[str, str]]) -> List[str]:
        return self.activated_memory_nodes

    def reinterpretation(self, conversation: List[Dict[str, str]]) -> str:
        nodes = self.retrieve_nodes(conversation)
    
        if not nodes:
            return ""

        prompt = (
            "Given the following memory snippets, produce concise guidance "
            "for how the agent should respond next.\n\n"
            f"Memory:\n{nodes}\n\nConversation:\n{conversation}"
        )
        return self.agent.run_sync(prompt)
    
    
    def save_nodes(self, conversation: List[Dict[str, str]]) -> None:
        self.activated_memory_nodes.append("New node placeholder")
