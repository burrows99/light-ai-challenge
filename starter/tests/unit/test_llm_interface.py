"""Unit tests for LLM Interface."""

import pytest

from light_agent.llm.mock_llm_client import MockLLMClient


def test_mock_llm_returns_action():
    """Test that mock LLM returns an action."""
    llm = MockLLMClient()
    
    response = llm.generate(
        messages=[{"role": "user", "content": "show invoices"}],
        tools=[]
    )
    
    assert "type" in response
    assert response["type"] in ["tool_call", "final_answer"]


def test_mock_llm_tool_call_format():
    """Test that tool_call response has correct format."""
    llm = MockLLMClient()
    
    response = llm.generate(
        messages=[{"role": "user", "content": "list pending invoices"}],
        tools=[{"name": "list_invoices"}]
    )
    
    # Should eventually trigger a tool call
    if response["type"] == "tool_call":
        assert "tool" in response
        assert "arguments" in response


def test_mock_llm_final_answer_format():
    """Test that final_answer response has correct format."""
    llm = MockLLMClient()
    
    # Create a conversation that leads to final answer
    messages = [
        {"role": "user", "content": "show invoices"},
        {"role": "assistant", "content": "calling list_invoices"},
        {"role": "tool", "content": "Found 5 invoices"}
    ]
    
    response = llm.generate(messages=messages, tools=[])
    
    # Should eventually give final answer
    if response["type"] == "final_answer":
        assert "content" in response


def test_mock_llm_handles_conversation():
    """Test that LLM can handle multi-turn conversation."""
    llm = MockLLMClient()
    
    messages = [
        {"role": "user", "content": "What invoices do we have?"}
    ]
    
    response1 = llm.generate(messages=messages, tools=[{"name": "list_invoices"}])
    assert "type" in response1
    
    # Add tool result
    messages.extend([
        {"role": "assistant", "content": str(response1)},
        {"role": "tool", "content": "invoice data"}
    ])
    
    response2 = llm.generate(messages=messages, tools=[])
    assert "type" in response2
