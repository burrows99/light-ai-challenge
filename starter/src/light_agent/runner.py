"""
Light Agent Runtime — Entry Point

This is the starting point for your implementation. Your task is to build
the agent runtime that orchestrates the loop between a user request, the
LLM, and the available tools.

You are free to:
  - Refactor this file completely
  - Create new modules, classes, and abstractions
  - Change function signatures
  - Add configuration, middleware, etc.

The only hard requirement: running the test scenarios should produce
a structured execution trace showing what happened.
"""

from pathlib import Path
from light_agent.mock_tools import MockToolExecutor
from light_agent.mock_llm import MockLLMClient
from light_agent.types import Message, ExecutionTrace
from light_agent.tools.tool_registry import ToolRegistry
from light_agent.runtime.agent_runtime import AgentRuntime
from light_agent.config.runtime_config import RuntimeConfig


def run_agent(user_request: str) -> ExecutionTrace:
    """
    Run the agent for a given user request.

    Uses Light AI's provided MockLLMClient and MockToolExecutor
    with our custom AgentRuntime orchestration.
    """
    # Setup paths
    base_path = Path(__file__).resolve().parent.parent.parent / "data"
    tools_path = base_path / "tools.json"
    mock_data_path = base_path / "mock_data.json"
    
    # Initialize components using Light AI's classes
    registry = ToolRegistry(str(tools_path))
    executor = MockToolExecutor(str(mock_data_path))
    llm = MockLLMClient()
    config = RuntimeConfig(max_iterations=10)
    
    # Run the agent
    runtime = AgentRuntime(llm, executor, registry, config)
    result = runtime.run(user_request)
    
    # Convert to ExecutionTrace format
    trace = ExecutionTrace(
        user_request=user_request,
        final_response=result.answer if result.success else None,
        tool_calls_made=len([s for s in result.trace.get('steps', []) if s.get('step_type') == 'tool_call']),
        error=result.error if not result.success else None
    )
    
    return trace


# Quick manual test
if __name__ == "__main__":
    scenarios = [
        "Show me all unpaid invoices over €5,000",
        "Find the largest pending invoice from Acme Corp and approve it",
        "Approve invoice INV-9999",
    ]

    for request in scenarios:
        print(f"\n{'='*60}")
        print(f"REQUEST: {request}")
        print(f"{'='*60}")
        try:
            trace = run_agent(request)
            print(f"RESPONSE: {trace.final_response}")
            print(f"TOOL CALLS: {trace.tool_calls_made}")
            print(f"DURATION: {trace.total_duration_ms:.0f}ms")
        except NotImplementedError:
            print("⚠  Not yet implemented")
        except Exception as e:
            print(f"ERROR: {e}")
