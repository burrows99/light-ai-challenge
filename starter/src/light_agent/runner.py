"""
Light Agent Runtime — Entry Point

This implementation demonstrates SOLID principles in action:
- Uses dependency injection with protocol abstractions
- Adapters wrap Light AI's concrete implementations
- Easy to swap components for testing or production use
- Clear separation of concerns throughout
"""

from pathlib import Path
from light_agent.mock_tools import MockToolExecutor
from light_agent.mock_llm import MockLLMClient
from light_agent.types import ExecutionTrace
from light_agent.tools.tool_registry import ToolRegistry
from light_agent.runtime.agent_runtime import AgentRuntime
from light_agent.config.runtime_config import RuntimeConfig

# Import adapters for dependency injection
from light_agent.adapters.light_ai_llm_adapter import LightAILLMAdapter
from light_agent.adapters.light_ai_tool_adapter import LightAIToolExecutorAdapter


def run_agent(user_request: str) -> ExecutionTrace:
    """
    Run the agent for a given user request.

    This function demonstrates the Dependency Inversion Principle:
    - AgentRuntime depends on LLMProvider and ToolExecutor abstractions
    - We inject concrete implementations via adapters
    - Easy to swap implementations without changing AgentRuntime
    """
    # Setup paths - data/ is in project root (parent of starter/)
    base_path = Path(__file__).resolve().parent.parent.parent.parent / "data"
    tools_path = base_path / "tools.json"
    mock_data_path = base_path / "mock_data.json"
    
    # Create Light AI's concrete implementations
    llm_client = MockLLMClient()
    tool_executor = MockToolExecutor(str(mock_data_path))
    
    # Wrap in adapters that implement our protocols
    llm_provider = LightAILLMAdapter(llm_client)
    executor = LightAIToolExecutorAdapter(tool_executor)
    
    # Other components
    registry = ToolRegistry(str(tools_path))
    config = RuntimeConfig(max_iterations=10)
    
    # Inject dependencies into runtime (Dependency Inversion Principle)
    runtime = AgentRuntime(llm_provider, executor, registry, config)
    result = runtime.run(user_request)
    
    # Calculate total duration from trace steps
    total_duration = sum(
        step.get('duration_ms', 0) 
        for step in result.trace.get('steps', [])
    )
    
    # Convert to ExecutionTrace format
    trace = ExecutionTrace(
        user_request=user_request,
        final_response=result.answer if result.success else None,
        tool_calls_made=len([s for s in result.trace.get('steps', []) if s.get('step_type') == 'tool_call']),
        total_duration_ms=total_duration if total_duration > 0 else None,
        error=result.error if not result.success else None
    )
    
    return trace


def main():
    """Entry point for the agent demonstration."""
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
            if trace.total_duration_ms is not None:
                print(f"DURATION: {trace.total_duration_ms:.0f}ms")
        except NotImplementedError:
            print("⚠  Not yet implemented")
        except Exception as e:
            print(f"ERROR: {e}")


if __name__ == "__main__":
    main()
