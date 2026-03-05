"""Adapter for Light AI's MockLLMClient."""

from typing import List

from light_agent.mock_llm import MockLLMClient
from light_agent.protocols.llm_protocol import LLMProvider
from light_agent.types import Message


class LightAILLMAdapter(LLMProvider):
    """Adapter that wraps Light AI's MockLLMClient to implement LLMProvider protocol.
    
    This adapter pattern allows us to use Light AI's provided implementation
    while maintaining loose coupling through the LLMProvider interface.
    
    Benefits:
    - AgentRuntime doesn't depend on Light AI's concrete classes
    - Easy to swap with real LLM providers later (OpenAI, Anthropic, etc.)
    - Maintains compatibility with Light AI's test infrastructure
    """
    
    def __init__(self, llm_client: MockLLMClient = None):
        """Initialize the adapter.
        
        Args:
            llm_client: Light AI's MockLLMClient instance. If None, creates a new one.
        """
        self._client = llm_client if llm_client is not None else MockLLMClient()
    
    def chat(self, messages: List[Message], tools: List[dict]) -> Message:
        """Generate a response using Light AI's MockLLMClient.
        
        Args:
            messages: Conversation history
            tools: Available tools that the LLM can call
            
        Returns:
            Message with either content (final answer) or tool_calls (actions to take)
        """
        return self._client.chat(messages, tools)
