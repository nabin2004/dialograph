from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, AIMessagePromptTemplate

class Agent:
    def __init__(self, args):
        self.args = args
        self.cost = 0 
    
    def next_action(self, conversation) -> str:
        raise NotImplementedError("Subclasses must implement this method.")
        
    def generate_prompt(self, prompt_template: dict[str, Any]) -> ChatPromptTemplate:
        messages = []
        messages.append(SystemMessagePromptTemplate.from_template(prompt_template["system"]))
        if "assistant" in prompt_template:
            messages.append(AIMessagePromptTemplate.from_template(prompt_template["assistant"]))    
        if "user" in prompt_template:
            messages.append(HumanMessagePromptTemplate.from_template(prompt_template["user"]))
        final_prompt_template = ChatPromptTemplate.from_messages(messages)
        return final_prompt_template
        

class DialographAgent:
    """
    Main agent class: proactive, curriculum-aware dialogue.
    Integrates graph memory + temporal dynamics + policy.
    """    
    def __init__(self, args):
        self.data_name = args.data_name
        self.api_key = args.api_key
        self.args = args 
        self.mode = args.mode 
        self.activate_top_k = args.activate_top_k
        self.activated_memory_nodes = []
        self.recontextualized_guidance = []
        
    def next_action(self, conversation) -> str:
        pass 

    def revision(self, conversation) -> str:
        pass

    def extract_from_failure(self, conversation) -> str:
        pass

    def extract_from_success(self, conversation) -> str:
        pass

    def retrieve_nodes(self, conversation) -> str:
        pass

    def reinterpretation(self, conversation) -> str:
        pass

    def save_nodes(self, conversation) -> str:
        pass