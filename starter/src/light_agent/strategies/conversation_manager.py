"""Conversation management strategy - handles message state."""

from typing import List

from light_agent.types import Message, ToolResult


class ConversationManager:
    """Manages conversation messages in the agent loop.
    
    This class follows the Single Responsibility Principle (SRP) by focusing
    solely on message state management. It decouples message handling from
    the main agent orchestration logic.
    
    Benefits:
    - Clear separation of concerns
    - Easy to test message handling independently
    - Can add features like message filtering, context window management
    - Simple interface for message operations
    """
    
    def __init__(self):
        """Initialize an empty conversation."""
        self._messages: List[Message] = []
    
    def add_user_message(self, content: str) -> None:
        """Add a user message to the conversation.
        
        Args:
            content: User's input text
        """
        self._messages.append(Message(role="user", content=content))
    
    def add_assistant_message(self, message: Message) -> None:
        """Add an assistant (LLM) message to the conversation.
        
        Args:
            message: LLM response (may contain tool calls or content)
        """
        self._messages.append(message)
    
    def add_tool_result(self, result: ToolResult, error_prefix: str = "Error") -> None:
        """Add a tool execution result to the conversation.
        
        Args:
            result: Result from tool execution
            error_prefix: Prefix to use for error messages
        """
        from light_agent.types import ToolCallStatus
        
        if result.status == ToolCallStatus.SUCCESS:
            content = str(result.result)
        else:
            error_msg = result.error or "Unknown error"
            content = f"{error_prefix}: {error_msg}"
        
        message = Message(role="tool", content=content, tool_result=result)
        self._messages.append(message)
    
    def get_messages(self) -> List[Message]:
        """Get all messages in the conversation.
        
        Returns:
            List of all messages
        """
        return self._messages.copy()
    
    def get_message_count(self) -> int:
        """Get the number of messages in the conversation.
        
        Returns:
            Total message count
        """
        return len(self._messages)
    
    def clear(self) -> None:
        """Clear all messages from the conversation."""
        self._messages.clear()
