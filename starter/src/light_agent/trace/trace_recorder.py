"""Trace recorder for agent execution observability."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class TraceRecorder:
    """Records execution traces for observability."""
    
    def __init__(self):
        """Initialize the trace recorder."""
        self.steps: List[Dict[str, Any]] = []
        self._step_counter = 0
    
    def record_step(
        self,
        step_type: str,
        tool: Optional[str] = None,
        arguments: Optional[Dict[str, Any]] = None,
        result: Optional[Any] = None,
        content: Optional[str] = None,
        duration_ms: Optional[float] = None,
        error: Optional[str] = None
    ) -> None:
        """Record a step in the agent execution.
        
        Args:
            step_type: Type of step (llm_decision, tool_call, final_answer, etc.)
            tool: Tool name (for tool_call steps)
            arguments: Tool arguments (for tool_call steps)
            result: Tool result (for tool_call steps)
            content: Text content (for llm_decision, final_answer steps)
            duration_ms: Duration in milliseconds
            error: Error message if step failed
        """
        self._step_counter += 1
        
        step = {
            "step_id": self._step_counter,
            "step_type": step_type,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if tool is not None:
            step["tool"] = tool
        if arguments is not None:
            step["arguments"] = arguments
        if result is not None:
            step["result"] = result
        if content is not None:
            step["content"] = content
        if duration_ms is not None:
            step["duration_ms"] = duration_ms
        if error is not None:
            step["error"] = error
        
        self.steps.append(step)
    
    def export(self) -> Dict[str, Any]:
        """Export trace to a dictionary.
        
        Returns:
            Dictionary containing all trace data
        """
        return {
            "steps": self.steps,
            "total_steps": len(self.steps)
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the trace.
        
        Returns:
            Summary statistics about the trace
        """
        tool_calls = sum(1 for step in self.steps if step["step_type"] == "tool_call")
        
        return {
            "total_steps": len(self.steps),
            "tool_calls": tool_calls
        }
