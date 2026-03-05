"""Agent runtime - orchestrates LLM and tool execution.

This module implements the core agent orchestration following SOLID principles:
- Single Responsibility: AgentRuntime focuses only on orchestration
- Open/Closed: Extensible through protocols without modifying core logic
- Liskov Substitution: Any LLMProvider/ToolExecutor implementation works
- Interface Segregation: Clean, focused interfaces
- Dependency Inversion: Depends on abstractions (protocols), not concrete classes
"""

from typing import Dict

from light_agent.config.runtime_config import RuntimeConfig
from light_agent.protocols.llm_protocol import LLMProvider
from light_agent.protocols.tool_executor_protocol import ToolExecutor
from light_agent.strategies.conversation_manager import ConversationManager
from light_agent.strategies.tool_orchestrator import ToolOrchestrator
from light_agent.tools.tool_registry import ToolRegistry


class AgentResult:
    """Result of an agent execution."""
    
    def __init__(self, success: bool, answer: str = "", trace: Dict = None, error: str = ""):
        self.success = success
        self.answer = answer
        self.trace = trace or {}
        self.error = error


class AgentRuntime:
    """Main agent runtime that orchestrates execution using dependency injection.
    
    This class demonstrates the Dependency Inversion Principle - it depends on
    abstractions (LLMProvider, ToolExecutor) rather than concrete implementations.
    This makes the runtime:
    - Highly testable (easy to mock dependencies)
    - Extensible (plug in different LLM providers or tool executors)
    - Maintainable (clear separation of concerns)
    """
    
    def __init__(
        self,
        llm_provider: LLMProvider,
        tool_executor: ToolExecutor,
        tool_registry: ToolRegistry,
        config: RuntimeConfig = None
    ):
        """Initialize the runtime with injected dependencies.
        
        Args:
            llm_provider: LLM provider implementation (abstraction, not concrete class)
            tool_executor: Tool executor implementation (abstraction, not concrete class)
            tool_registry: Tool registry for loading tool definitions
            config: Runtime configuration
        """
        self._llm = llm_provider
        self._tool_executor = tool_executor
        self._registry = tool_registry
        self._config = config or RuntimeConfig()
    
    def run(self, user_input: str) -> AgentResult:
        """Run the agent on a user input using the ReAct pattern.
        
        This method implements a clean ReAct (Reason → Act → Observe) loop with:
        - Clear separation of concerns through strategy classes
        - Dependency injection for flexibility
        - Comprehensive tracing for observability
        
        Args:
            user_input: User's question or command
            
        Returns:
            AgentResult with the outcome
        """
        from light_agent.trace.trace_recorder import TraceRecorder
        
        # Initialize components following SRP
        trace = TraceRecorder()
        conversation = ConversationManager()
        orchestrator = ToolOrchestrator(self._tool_executor, trace)
        
        # Start conversation with user input
        conversation.add_user_message(user_input)
        
        trace.record_step(
            step_type="start",
            content=f"User input: {user_input}"
        )
        
        iteration = 0
        
        try:
            while iteration < self._config.max_iterations:
                iteration += 1
                
                # Prepare tools for LLM (convert from registry format)
                tools = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters.model_dump()
                    }
                    for tool in self._registry.get_all_tools()
                ]
                
                # REASON: Ask LLM to decide next action
                trace.record_step(
                    step_type="llm_decision",
                    content=f"Iteration {iteration}: Requesting LLM decision"
                )
                
                response = self._llm.chat(conversation.get_messages(), tools)
                conversation.add_assistant_message(response)
                
                # Check if LLM wants to ACT (call tools)
                if response.tool_calls:
                    # ACT: Execute tool calls through orchestrator
                    results = orchestrator.execute_tool_calls(response.tool_calls)
                    
                    # OBSERVE: Add results back to conversation
                    for result in results:
                        conversation.add_tool_result(result)
                
                elif response.content:
                    # Final answer reached
                    trace.record_step(
                        step_type="final_answer",
                        content=f"Final answer: {response.content[:100]}"
                    )
                    
                    return AgentResult(
                        success=True,
                        answer=response.content,
                        trace=trace.export()
                    )
            
            # Max iterations reached without final answer
            return AgentResult(
                success=False,
                error=f"Max iterations ({self._config.max_iterations}) reached",
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
