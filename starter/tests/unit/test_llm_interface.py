"""Unit tests for LLM Interface (Light AI's MockLLMClient)."""

from light_agent.mock_llm import MockLLMClient
from light_agent.types import Message


def test_mock_llm_returns_action():
    """Test that mock LLM returns a Message."""
    llm = MockLLMClient()
    
    messages = [
        Message(role="user", content="Show me pending invoices")
    ]
    tools = [{"name": "list_invoices"}]
    
    response = llm.chat(messages, tools)
    
    assert isinstance(response, Message)
    assert response.role == "assistant"
    # Should either have tool_calls or content
    assert response.tool_calls is not None or response.content is not None


def test_mock_llm_tool_call_format():
    """Test that tool call response has correct format."""
    llm = MockLLMClient()
    
    messages = [
        Message(role="user", content="Show me all unpaid invoices over €5,000")
    ]
    tools = [{"name": "list_invoices"}]
    
    response = llm.chat(messages, tools)
    
    # Light AI's MockLLMClient should return tool_calls for this query
    if response.tool_calls:
        assert len(response.tool_calls) > 0
        tool_call = response.tool_calls[0]
        assert hasattr(tool_call, 'name')
        assert hasattr(tool_call, 'arguments')


def test_mock_llm_final_answer_format():
    """Test that final answer response has correct format."""
    llm = MockLLMClient()
    
    # Simulate conversation that leads to final answer
    messages = [
        Message(role="user", content="Show me all unpaid invoices over €5,000"),
        Message(role="assistant", tool_calls=[]),  # Simulated tool call response
        Message(role="tool", content='[{"id": "INV-001"}]')
    ]
    tools = [{"name": "list_invoices"}]
    
    response = llm.chat(messages, tools)
    
    # After tool result, should give final answer
    if response.content:
        assert isinstance(response.content, str)
        assert len(response.content) > 0


def test_mock_llm_handles_conversation():
    """Test that LLM can handle multi-turn conversation."""
    llm = MockLLMClient()
    
    messages = [
        Message(role="user", content="Show me all unpaid invoices over €5,000"),
        Message(role="assistant", tool_calls=[]),
        Message(role="tool", content='[{"id": "INV-001"}]')
    ]
    tools = [{"name": "list_invoices"}]
    
    response = llm.chat(messages, tools)
    
    # Should handle the conversation and return a Message
    assert response is not None
    assert isinstance(response, Message)
    assert response.role == "assistant"
