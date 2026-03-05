"""Protocol for tool executor abstraction."""

from abc import ABC, abstractmethod
from typing import Any, Dict

from light_agent.types import ToolResult


class ToolExecutor(ABC):
    """Abstract interface for tool execution.
    
    This protocol enables dependency inversion - separating the tool execution
    interface from its implementation. This allows for:
    - Different execution strategies (sync, async, parallel)
    - Easy mocking in tests
    - Adding middleware (logging, retry, rate limiting, caching)
    - Supporting different tool backends
    
    Benefits:
    - Testability: Mock tool execution without external dependencies
    - Flexibility: Swap implementations based on environment (dev, staging, prod)
    - Extensibility: Add cross-cutting concerns without modifying executors
    """
    
    @abstractmethod
    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        """Execute a tool with given arguments.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments as key-value pairs
            
        Returns:
            ToolResult with status, result data, or error
        """
        pass
