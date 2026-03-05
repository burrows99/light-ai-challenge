"""Tool orchestration strategy - coordinates tool execution."""

from typing import List, Optional

from light_agent.protocols.tool_executor_protocol import ToolExecutor
from light_agent.trace.trace_recorder import TraceRecorder
from light_agent.types import ToolCall, ToolResult, ToolCallStatus


class ToolOrchestrator:
    """Orchestrates tool execution with tracing and error handling.
    
    This class follows the Single Responsibility Principle (SRP) by focusing
    on tool execution coordination. It decouples tool execution logic from
    the main agent loop, making both easier to understand and test.
    
    Benefits:
    - Centralized tool execution logic
    - Consistent error handling across all tool calls
    - Easy to add features like parallel execution, retries, timeouts
    - Simplified testing of tool execution paths
    """
    
    def __init__(
        self,
        executor: ToolExecutor,
        trace_recorder: Optional[TraceRecorder] = None
    ):
        """Initialize the orchestrator.
        
        Args:
            executor: Tool executor implementation (injected dependency)
            trace_recorder: Optional trace recorder for observability
        """
        self._executor = executor
        self._trace = trace_recorder
    
    def execute_tool_calls(
        self,
        tool_calls: List[ToolCall]
    ) -> List[ToolResult]:
        """Execute multiple tool calls sequentially.
        
        Args:
            tool_calls: List of tool calls to execute
            
        Returns:
            List of tool results (one per call)
        """
        results = []
        
        for tool_call in tool_calls:
            result = self._execute_single_tool(tool_call)
            results.append(result)
        
        return results
    
    def _execute_single_tool(self, tool_call: ToolCall) -> ToolResult:
        """Execute a single tool call with tracing.
        
        Args:
            tool_call: Tool call to execute
            
        Returns:
            Tool result
        """
        # Record the tool call attempt
        if self._trace:
            self._trace.record_step(
                step_type="tool_call",
                content=f"Calling tool: {tool_call.name}",
                tool=tool_call.name,
                arguments=tool_call.arguments
            )
        
        # Execute the tool
        try:
            result = self._executor.execute(tool_call.name, tool_call.arguments)
        except Exception as e:
            # Wrap exceptions as ToolResult errors
            result = ToolResult(
                tool_name=tool_call.name,
                status=ToolCallStatus.ERROR,
                error=f"Execution failed: {str(e)}"
            )
        
        # Record the result
        if self._trace:
            if result.status == ToolCallStatus.SUCCESS:
                self._trace.record_step(
                    step_type="tool_result",
                    content=f"Tool result: {str(result.result)[:100]}",
                    tool=tool_call.name,
                    result=result.result
                )
            else:
                error_msg = result.error or "Unknown error"
                self._trace.record_step(
                    step_type="tool_error",
                    content=f"Tool error: {error_msg}",
                    tool=tool_call.name,
                    error=error_msg
                )
        
        return result
