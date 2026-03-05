"""CLI runner for interactive agent testing."""

import sys
from pathlib import Path

from light_agent.config.runtime_config import RuntimeConfig
from light_agent.mock_llm import MockLLMClient
from light_agent.mock_tools import MockToolExecutor
from light_agent.runtime.agent_runtime import AgentRuntime
from light_agent.tools.tool_registry import ToolRegistry


def build_runtime() -> AgentRuntime:
    """Build a complete runtime."""
    # Find data directory (relative to project root)
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent.parent.parent
    data_path = project_root / "data"
    
    tools_path = data_path / "tools.json"
    mock_data_path = data_path / "mock_data.json"
    
    if not tools_path.exists():
        raise FileNotFoundError(f"Tools file not found: {tools_path}")
    if not mock_data_path.exists():
        raise FileNotFoundError(f"Mock data file not found: {mock_data_path}")
    
    registry = ToolRegistry(str(tools_path))
    executor = ToolExecutor(registry, str(mock_data_path))
    llm = MockLLMClient()
    config = RuntimeConfig(max_iterations=10)
    
    return AgentRuntime(llm, registry, executor, config)


def print_trace(trace: dict) -> None:
    """Print execution trace in a readable format."""
    print("\n=== Execution Trace ===")
    for i, step in enumerate(trace.get("steps", []), 1):
        step_type = step.get("step_type", "unknown")
        print(f"\nStep {i}: {step_type}")
        
        if step_type == "tool_call":
            print(f"  Tool: {step.get('tool')}")
            print(f"  Arguments: {step.get('arguments')}")
        elif step_type == "tool_result":
            result = step.get('result')
            if isinstance(result, list):
                print(f"  Result: Found {len(result)} items")
            else:
                print(f"  Result: {result}")
        elif step_type == "final_answer":
            print(f"  Answer: {step.get('content')}")
        elif step_type == "tool_error":
            print(f"  Error: {step.get('error')}")
    
    print(f"\nTotal steps: {trace.get('total_steps', 0)}")


def main():
    """Run the interactive CLI."""
    print("=" * 60)
    print("Light Agent Runtime - Interactive Sandbox")
    print("=" * 60)
    print("\nBuilding runtime...")
    
    try:
        runtime = build_runtime()
        print("✓ Runtime initialized successfully")
        print("\nAvailable tools:")
        for tool in runtime.registry.get_all_tools():
            print(f"  - {tool.name}: {tool.description[:60]}...")
    except Exception as e:
        print(f"✗ Failed to initialize runtime: {e}")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("Enter your query (or 'quit' to exit)")
    print("=" * 60)
    
    while True:
        try:
            user_input = input("\n>>> ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break
            
            print(f"\nProcessing: {user_input}")
            print("-" * 60)
            
            result = runtime.run(user_input)
            
            if result.success:
                print(f"\n✓ Success!")
                print(f"\nAnswer: {result.answer}")
            else:
                print(f"\n✗ Failed: {result.error}")
            
            # Show trace
            print_trace(result.trace)
            
            print("\n" + "=" * 60)
            
        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n✗ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
