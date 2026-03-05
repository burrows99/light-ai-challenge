#!/usr/bin/env python3
"""Simple test script to verify the agent runtime works."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from light_agent.config.runtime_config import RuntimeConfig
from light_agent.llm.mock_llm_client import MockLLMClient
from light_agent.runtime.agent_runtime import AgentRuntime
from light_agent.tools.tool_executor import ToolExecutor
from light_agent.tools.tool_registry import ToolRegistry


def main():
    """Quick test of the runtime."""
    # Load from parent directory
    base_path = Path(__file__).parent.parent / "data"
    
    print("Loading tools and data...")
    registry = ToolRegistry(str(base_path / "tools.json"))
    executor = ToolExecutor(registry, str(base_path / "mock_data.json"))
    llm = MockLLMClient()
    config = RuntimeConfig(max_iterations=5)
    
    runtime = AgentRuntime(llm, registry, executor, config)
    
    print("\n=== Testing Agent Runtime ===\n")
    
    test_queries = [
        "Show me pending invoices",
        "List all invoices from Acme Corp",
    ]
    
    for query in test_queries:
        print(f"Query: {query}")
        print("-" * 60)
        
        result = runtime.run(query)
        
        if result.success:
            print(f"✓ Success")
            print(f"Answer: {result.answer[:100]}...")
        else:
            print(f"✗ Failed: {result.error}")
        
        print(f"Steps: {result.trace.get('total_steps', 0)}")
        print()


if __name__ == "__main__":
    main()
