"""Unit tests for adapter error handling."""

from light_agent.adapters.light_ai_tool_adapter import LightAIToolExecutorAdapter


def test_adapter_requires_executor_or_path():
    """Test that adapter requires either executor or mock_data_path."""
    try:
        adapter = LightAIToolExecutorAdapter()
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Must provide either executor or mock_data_path" in str(e)
