"""Unit tests for Tool Registry."""
import pytest
from pathlib import Path
from light_agent.tools.tool_registry import ToolRegistry


def test_load_tools():
    """Test loading tools from JSON file."""
    tools_path = Path(__file__).parent.parent.parent.parent / "data" / "tools.json"
    registry = ToolRegistry(str(tools_path))
    
    tools = registry.list_tools()
    
    assert "list_invoices" in tools
    assert "approve_invoice" in tools
    assert "get_invoice" in tools
    assert "send_notification" in tools
    assert "get_current_user" in tools


def test_get_tool():
    """Test retrieving a specific tool."""
    tools_path = Path(__file__).parent.parent.parent.parent / "data" / "tools.json"
    registry = ToolRegistry(str(tools_path))
    
    tool = registry.get_tool("list_invoices")
    
    assert tool is not None
    assert tool.name == "list_invoices"
    assert "Search and list invoices" in tool.description
    assert tool.metadata.mutating is False


def test_get_nonexistent_tool():
    """Test that getting a nonexistent tool raises error."""
    tools_path = Path(__file__).parent.parent.parent.parent / "data" / "tools.json"
    registry = ToolRegistry(str(tools_path))
    
    with pytest.raises(ValueError, match="Tool not found"):
        registry.get_tool("nonexistent_tool")


def test_get_all_tools():
    """Test retrieving all tool objects."""
    tools_path = Path(__file__).parent.parent.parent.parent / "data" / "tools.json"
    registry = ToolRegistry(str(tools_path))
    
    tools = registry.get_all_tools()
    
    assert len(tools) == 5
    assert all(hasattr(tool, 'name') for tool in tools)
