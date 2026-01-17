from turtle import done
import json
from dataclasses import dataclass, field
from typing import List, Dict, Any
import random

@dataclass
class State:
    """
    Represents the state of the dialogue environment.

    Attributes:
    - topic: conversation topic information
    - conversation: list of exchanged messages
    - conversation_w_strategy: list of exchanged messages with strategies
    - rewards: list of rewards obtained at each step
    - current_step: current step in the dialogue
    - done: whether the dialogue has ended
    - failed: whether the dialogue has failed
    """
    topic: Dict[str, str] = field(default_factory=dict)
    conversation: List[Dict[str, str]] = field(default_factory=list)
    conversation_w_strategy: List[Dict[str, str]] = field(default_factory=list)
    rewards: List[float] = field(default_factory=list)
    current_step: int = 0
    done: bool = False
    failed: bool = False


class Env:
    """
    The dialogue world where agent interacts.
    Attributes:
    - 
    - reset: pick a new case, clear state, prepare the first messages.
    - step: take an action, update state, return observation, reward, done.
    - done: check if the episode is finished.
    - backtrack: revert to previous state if needed.
    - calculate_reward: compute reward based on current state.
    - render: visualize the current state.
    """
    def __init__(self, dataset, mode='train', data_name='esc', max_turns=5, start_episode=1):
        self.dataset = dataset[mode]
        self.mode = mode
        self.data_name = data_name
        self.max_turns = max_turns
        self.case = None
        self.start_episode = start_episode
        self.train_num = start_episode - 1
        self.test_num = start_episode - 1
        self.state = State()



    def reset(self):
        """Start a new episode: pick a case, reset state, initialize first conversation."""
        self.state = State()  # reset state completely

        # Pick a case
        if self.mode == 'train':
            self.case = random.choice(self.dataset)
        elif self.mode == 'test':
            self.case = self.dataset[self.test_num]
            self.test_num += 1
        else:
            raise ValueError(f"Unknown mode: {self.mode}")

        # Save case info
        self.state.case_info = self.case

        # Initialize conversation
        if self.data_name in ['esc', 'extes']:
            self.state.conversation = [{
                "role": "Patient",
                "content": self.case.get("situation", "")
            }]
        elif self.data_name in ['p4g', 'p4gplus']:
            self.state.conversation = [
                {"role": "Persuader", "content": self.case['dialog'][0]['text']},
                {"role": "Persuadee", "content": self.case['dialog'][1]['text']}
            ]
        else:
            raise ValueError(f"Unknown data_name: {self.data_name}")

        return self.state

    def step(self, action: str):
        """Simulate one turn: agent acts, user replies, update state and rewards."""
        if self.state.done:
            print("Episode already done. Call reset() to start a new episode.")
            return self.state

        # Agent action
        agent_role = "Therapist" if self.data_name in ['esc', 'extes'] else "Persuader"
        self.state.conversation.append({"role": agent_role, "content": action})
        self.state.conversation_w_strategy.append({"role": agent_role, "content": action, "strategy": action})

        # Simulated user reply (for now, just placeholder)
        user_role = "Patient" if self.data_name in ['esc', 'extes'] else "Persuadee"
        user_reply = f"User responds to '{action}'"
        self.state.conversation.append({"role": user_role, "content": user_reply})
        self.state.conversation_w_strategy.append({"role": user_role, "content": user_reply, "strategy": ""})

        # Update step count
        self.state.curr_step += 1

        # Simple reward: +1 per turn (placeholder)
        reward = 1.0
        self.state.rewards.append(reward)

        # Check if episode is done
        if self.state.curr_step >= self.max_turns:
            self.state.done = True

        return self.state

    def done(self):
        """Return True if episode is finished, False otherwise."""
        return self.state.done or self.state.curr_step >= self.max_turns

    def backtrack(self):
        raise NotImplementedError

    def calculate_reward(self):
        raise NotImplementedError

    def render(self):
        """
        visualize the current state of the environment
        """
        raise NotImplementedError

