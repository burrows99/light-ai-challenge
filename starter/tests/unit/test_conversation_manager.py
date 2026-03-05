"""Unit tests for ConversationManager."""

from light_agent.strategies.conversation_manager import ConversationManager
from light_agent.types import Message, ToolResult, ToolCallStatus


def test_add_user_message():
    """Test adding a user message."""
    manager = ConversationManager()
    manager.add_user_message("Hello")
    
    messages = manager.get_messages()
    assert len(messages) == 1
    assert messages[0].role == "user"
    assert messages[0].content == "Hello"


def test_add_assistant_message():
    """Test adding an assistant message."""
    manager = ConversationManager()
    assistant_msg = Message(role="assistant", content="Hi there")
    manager.add_assistant_message(assistant_msg)
    
    messages = manager.get_messages()
    assert len(messages) == 1
    assert messages[0].role == "assistant"


def test_add_tool_result_success():
    """Test adding a successful tool result."""
    manager = ConversationManager()
    result = ToolResult(
        tool_name="test_tool",
        status=ToolCallStatus.SUCCESS,
        result={"data": "test"}
    )
    manager.add_tool_result(result)
    
    messages = manager.get_messages()
    assert len(messages) == 1
    assert messages[0].role == "tool"
    assert "data" in messages[0].content


def test_add_tool_result_error():
    """Test adding an error tool result."""
    manager = ConversationManager()
    result = ToolResult(
        tool_name="test_tool",
        status=ToolCallStatus.ERROR,
        error="Something went wrong"
    )
    manager.add_tool_result(result, error_prefix="Error")
    
    messages = manager.get_messages()
    assert len(messages) == 1
    assert "Error:" in messages[0].content
    assert "Something went wrong" in messages[0].content


def test_get_message_count():
    """Test getting message count."""
    manager = ConversationManager()
    assert manager.get_message_count() == 0
    
    manager.add_user_message("Test")
    assert manager.get_message_count() == 1
    
    manager.add_user_message("Test 2")
    assert manager.get_message_count() == 2


def test_clear():
    """Test clearing messages."""
    manager = ConversationManager()
    manager.add_user_message("Test 1")
    manager.add_user_message("Test 2")
    assert manager.get_message_count() == 2
    
    manager.clear()
    assert manager.get_message_count() == 0
    assert len(manager.get_messages()) == 0


def test_get_messages_returns_copy():
    """Test that get_messages returns a copy, not the original list."""
    manager = ConversationManager()
    manager.add_user_message("Test")
    
    messages1 = manager.get_messages()
    messages2 = manager.get_messages()
    
    # Should be equal but not the same object
    assert messages1 == messages2
    assert messages1 is not messages2
