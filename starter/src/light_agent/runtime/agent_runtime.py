"""Agent runtime - orchestrates LLM and tool execution."""

from typing import Any, Dict, List

from light_agent.config.runtime_config import RuntimeConfig
from light_agent.mock_llm import MockLLMClient
from light_agent.mock_tools import MockToolExecutor
from light_agent.types import Message, ToolCall, ToolResult, ToolCallStatus, ExecutionTrace
from light_agent.tools.tool_registry import ToolRegistry


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
        tool_executor: MockToolExecutor,
        tool_registry: ToolRegistry,
        config: RuntimeConfig = None
    ):
        """Initialize the runtime.
        
        Args:
            llm_client: LLM client instance
            tool_executor: Tool executor from Light AI
            tool_registry: Tool registry
            config: Runtime configuration
        """
        self.llm = llm_client
        self.executor = tool_executor
        self.registry = tool_registry
        self.config = config or RuntimeConfig()
    
    def run(self, user_input: str) -> AgentResult:
        """Run the agent on a user input.
        
        Args:
            user_input: User's question or command
            
        Returns:
            AgentResult with the outcome
        """
        from light_agent.trace.trace_recorder import TraceRecorder
        trace = TraceRecorder()
        messages: List[Message] = [
            Message(role="user", content=user_input)
        ]
        
        trace.record_step(
            step_type="start",
            content=f"User input: {user_input}"
        )
        
        iteration = 0
        
        try:
            while iteration < self.config.max_iterations:
                iteration += 1
                
                # Get available tools for Light AI's MockLLMClient
                tools = [
                    {"name": tool.name, "description": tool.description, "parameters": tool.parameters.model_dump()}
                    for tool in self.registry.get_all_tools()
                ]
                
                # LLM decision
                trace.record_step(
                    step_type="llm_decision",
                    content=f"Iteration {iteration}: Requesting LLM decision"
                )
                
                # Use Light AI's MockLLMClient.chat() method
                response = self.llm.chat(messages, tools)
                messages.append(response)
                
                # Check if LLM wants to call tools
                if response.tool_calls:
                    # Execute each tool call
                    for tool_call in response.tool_calls:
                        trace.record_step(
                            step_type="tool_call",
                            content=f"Calling tool: {tool_call.name}",
                            tool=tool_call.name,
                            arguments=tool_call.arguments
                        )
                        
                        # Use Light AI's MockToolExecutor.execute()
                        tool_result = self.executor.execute(tool_call.name, tool_call.arguments)
                        
                        # Add tool result to messages
                        from light_agent.types import ToolCallStatus
                        if tool_result.status == ToolCallStatus.SUCCESS:
                            result_msg = Message(
                                role="tool",
                                content=str(tool_result.result),
                                tool_result=tool_result
                            )
                            messages.append(result_msg)
                            
                            trace.record_step(
                                step_type="tool_result",
                                content=f"Tool result: {str(tool_result.result)[:100]}",
                                tool=tool_call.name,
                                result=tool_result.result
                            )
                        else:
                            error_msg = tool_result.error or "Unknown error"
                            result_msg = Message(
                                role="tool",
                                content=f"Error: {error_msg}",
                                tool_result=tool_result
                            )
                            messages.append(result_msg)
                            
                            trace.record_step(
                                step_type="tool_error",
                                content=f"Tool error: {error_msg}",
                                tool=tool_call.name,
                                error=error_msg
                            )
                
                elif response.content:
                    # Got final answer
                    trace.record_step(
                        step_type="final_answer",
                        content=f"Final answer: {response.content[:100]}"
                    )
                    
                    return AgentResult(
                        success=True,
                        answer=response.content,
                        trace=trace.export()
                    )
            
            # Max iterations reached
            return AgentResult(
                success=False,
                error=f"Max iterations ({self.config.max_iterations}) reached",
                trace=trace.export()
            )
            
        except Exception as e:
            trace.record_step(
                step_type="error",
                content=str(e)
            )
            
            return AgentResult(
                success=False,
                error=f"Runtime error: {str(e)}",
                trace=trace.export()
            )
