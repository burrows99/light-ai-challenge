"""Agent runtime - orchestrates LLM and tool execution."""

from typing import Any, Dict, List

from light_agent.config.runtime_config import RuntimeConfig
from light_agent.llm.mock_llm_client import MockLLMClient
from light_agent.tools.tool_executor import ToolExecutor
from light_agent.tools.tool_registry import ToolRegistry
from light_agent.trace.trace_recorder import TraceRecorder


class AgentResult:
    """Result of an agent execution."""
    
    def __init__(self, success: bool, answer: str = "", trace: Dict = None, error: str = ""):
        self.success = success
        self.answer = answer
        self.trace = trace or {}
        self.error = error


class AgentRuntime:
    """Main agent runtime that orchestrates execution."""
    
    def __init__(
        self,
        llm_client: MockLLMClient,
        tool_registry: ToolRegistry,
        tool_executor: ToolExecutor,
        config: RuntimeConfig = None
    ):
        """Initialize the runtime.
        
        Args:
            llm_client: LLM client instance
            tool_registry: Tool registry
            tool_executor: Tool executor
            config: Runtime configuration
        """
        self.llm = llm_client
        self.registry = tool_registry
        self.executor = tool_executor
        self.config = config or RuntimeConfig()
    
    def run(self, user_input: str) -> AgentResult:
        """Run the agent on a user input.
        
        Args:
            user_input: User's question or command
            
        Returns:
            AgentResult with the outcome
        """
        trace = TraceRecorder()
        messages: List[Dict[str, str]] = [
            {"role": "user", "content": user_input}
        ]
        
        trace.record_step(
            step_type="start",
            content=f"User input: {user_input}"
        )
        
        iteration = 0
        
        try:
            while iteration < self.config.max_iterations:
                iteration += 1
                
                # Get available tools
                tools = [
                    {"name": tool.name, "description": tool.description}
                    for tool in self.registry.get_all_tools()
                ]
                
                # LLM decision
                trace.record_step(
                    step_type="llm_decision",
                    content=f"Iteration {iteration}: Requesting LLM decision"
                )
                
                response = self.llm.generate(messages=messages, tools=tools)
                
                if response["type"] == "tool_call":
                    # Execute tool
                    tool_name = response["tool"]
                    arguments = response.get("arguments", {})
                    
                    trace.record_step(
                        step_type="tool_call",
                        tool=tool_name,
                        arguments=arguments
                    )
                    
                    try:
                        result = self.executor.execute(tool_name, arguments)
                        
                        trace.record_step(
                            step_type="tool_result",
                            tool=tool_name,
                            result=result
                        )
                        
                        # Add to conversation
                        messages.append({
                            "role": "assistant",
                            "content": f"Calling {tool_name}"
                        })
                        messages.append({
                            "role": "tool",
                            "content": str(result)
                        })
                        
                    except Exception as e:
                        error_msg = str(e)
                        trace.record_step(
                            step_type="tool_error",
                            tool=tool_name,
                            error=error_msg
                        )
                        
                        return AgentResult(
                            success=False,
                            error=f"Tool execution failed: {error_msg}",
                            trace=trace.export()
                        )
                
                elif response["type"] == "final_answer":
                    # Done!
                    answer = response.get("content", "")
                    
                    trace.record_step(
                        step_type="final_answer",
                        content=answer
                    )
                    
                    return AgentResult(
                        success=True,
                        answer=answer,
                        trace=trace.export()
                    )
                
                else:
                    raise ValueError(f"Unknown response type: {response['type']}")
            
            # Max iterations reached
            return AgentResult(
                success=False,
                error=f"Max iterations ({self.config.max_iterations}) reached",
                trace=trace.export()
            )
            
        except Exception as e:
            trace.record_step(
                step_type="error",
                error=str(e)
            )
            
            return AgentResult(
                success=False,
                error=f"Runtime error: {str(e)}",
                trace=trace.export()
            )
