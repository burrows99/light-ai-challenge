"""Protocol for LLM provider abstraction."""

from abc import ABC, abstractmethod
from typing import List

from light_agent.types import Message


class LLMProvider(ABC):
    """Abstract interface for LLM providers.
    
    This protocol enables dependency inversion - the AgentRuntime depends on
    this abstraction rather than concrete implementations. This makes it easy
    to swap LLM providers (Light AI, OpenAI, Anthropic, local models) without
    modifying the core agent logic.
    
    Benefits:
    - Easy testing with mock implementations
    - Support for multiple LLM backends
    - Clear contract for what an LLM provider must provide
    """
    
    @abstractmethod
    def chat(self, messages: List[Message], tools: List[dict]) -> Message:
        """Generate a response given conversation history and available tools.
        
        Args:
            messages: Conversation history
            tools: Available tools that the LLM can call
            
        Returns:
            Message with either content (final answer) or tool_calls (actions to take)
        """
        pass
