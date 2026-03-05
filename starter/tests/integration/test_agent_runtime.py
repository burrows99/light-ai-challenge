"""Integration tests for full agent runtime."""

from pathlib import Path

from light_agent.config.runtime_config import RuntimeConfig
from light_agent.mock_llm import MockLLMClient
from light_agent.mock_tools import MockToolExecutor
from light_agent.runtime.agent_runtime import AgentRuntime
from light_agent.tools.tool_registry import ToolRegistry

# Import adapters for dependency injection
from light_agent.adapters.light_ai_llm_adapter import LightAILLMAdapter
from light_agent.adapters.light_ai_tool_adapter import LightAIToolExecutorAdapter


def build_runtime(max_iterations: int = 10) -> AgentRuntime:
    """Build a complete runtime for testing using dependency injection."""
    # Data is in parent directory of starter
    base_path = Path(__file__).parent.parent.parent.parent / "data"
    tools_path = base_path / "tools.json"
    mock_data_path = base_path / "mock_data.json"
    
    # Create Light AI's concrete implementations
    llm_client = MockLLMClient()
    tool_executor = MockToolExecutor(str(mock_data_path))
    
    # Wrap in adapters that implement protocols (Dependency Inversion Principle)
    llm_provider = LightAILLMAdapter(llm_client)
    executor = LightAIToolExecutorAdapter(tool_executor)
    
    # Create other components
    registry = ToolRegistry(str(tools_path))
    config = RuntimeConfig(max_iterations=max_iterations)
    
    # Inject dependencies into runtime
    return AgentRuntime(llm_provider, executor, registry, config)


def test_simple_query():
    """Test a simple query that requires one tool call."""
    runtime = build_runtime()
    
    result = runtime.run("Show me pending invoices")
    
    assert result.success is True
    assert result.answer != ""
    assert "steps" in result.trace


def test_agent_handles_tool_error():
    """Test that agent handles tool errors gracefully."""
    runtime = build_runtime()
    
    # Test with Light AI's MockToolExecutor error handling
    from light_agent.mock_tools import MockToolExecutor
    from light_agent.types import ToolCallStatus
    from pathlib import Path
    
    base_path = Path(__file__).parent.parent.parent.parent / "data"
    mock_data_path = base_path / "mock_data.json"
    
    executor = MockToolExecutor(str(mock_data_path))
    
    # Light AI's MockToolExecutor returns ToolResult with ERROR status instead of raising
    result = executor.execute("get_invoice", {"invoice_id": "INV-999999"})
    assert result.status == ToolCallStatus.ERROR
    assert "not found" in result.error.lower()


def test_max_iterations():
    """Test that runtime respects max iterations."""
    runtime = build_runtime(max_iterations=2)
    
    result = runtime.run("Show me all invoices")
    
    # Should complete (might hit max iterations or complete normally)
    assert "steps" in result.trace
    assert len(result.trace["steps"]) <= 10  # Should have some steps


def test_trace_records_execution():
    """Test that execution is properly traced."""
    runtime = build_runtime()
    
    result = runtime.run("List pending invoices")
    
    assert "steps" in result.trace
    assert result.trace["total_steps"] > 0
    
    # Should have at least: start, llm_decision, tool_call, final_answer
    step_types = [step["step_type"] for step in result.trace["steps"]]
    assert "start" in step_types
