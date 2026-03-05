"""Adapter for Light AI's MockToolExecutor."""

from typing import Any, Dict

from light_agent.mock_tools import MockToolExecutor
from light_agent.protocols.tool_executor_protocol import ToolExecutor
from light_agent.types import ToolResult


class LightAIToolExecutorAdapter(ToolExecutor):
    """Adapter that wraps Light AI's MockToolExecutor to implement ToolExecutor protocol.
    
    This adapter pattern allows us to use Light AI's provided tool execution
    while maintaining loose coupling through the ToolExecutor interface.
    
    Benefits:
    - Core logic doesn't depend on Light AI's concrete implementation
    - Easy to add real tool execution later (API calls, database queries, etc.)
    - Can add middleware (retry, timeout, logging) without modifying Light AI's code
    - Maintains compatibility with Light AI's test infrastructure
    """
    
    def __init__(self, executor: MockToolExecutor = None, mock_data_path: str = None):
        """Initialize the adapter.
        
        Args:
            executor: Light AI's MockToolExecutor instance. If None, creates a new one.
            mock_data_path: Path to mock_data.json (only used if executor is None)
        """
        if executor is not None:
            self._executor = executor
        elif mock_data_path is not None:
            self._executor = MockToolExecutor(mock_data_path)
        else:
            raise ValueError("Must provide either executor or mock_data_path")
    
    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        """Execute a tool using Light AI's MockToolExecutor.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments as key-value pairs
            
        Returns:
            ToolResult with status, result data, or error
        """
        return self._executor.execute(tool_name, arguments)
