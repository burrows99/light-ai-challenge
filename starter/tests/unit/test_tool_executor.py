"""Unit tests for Tool Executor."""

from pathlib import Path

import pytest

from light_agent.tools.tool_registry import ToolRegistry
from light_agent.tools.tool_executor import ToolExecutor


def test_list_pending_invoices():
    """Test listing pending invoices."""
    tools_path = Path(__file__).parent.parent.parent.parent / "data" / "tools.json"
    mock_data_path = Path(__file__).parent.parent.parent.parent / "data" / "mock_data.json"
    
    registry = ToolRegistry(str(tools_path))
    executor = ToolExecutor(registry, str(mock_data_path))
    
    result = executor.execute("list_invoices", {"status": "pending"})
    
    assert isinstance(result, list)
    assert len(result) > 0
    # All returned invoices should have pending status
    for invoice in result:
        assert invoice["status"] == "pending"


def test_get_specific_invoice():
    """Test getting a specific invoice by ID."""
    tools_path = Path(__file__).parent.parent.parent.parent / "data" / "tools.json"
    mock_data_path = Path(__file__).parent.parent.parent.parent / "data" / "mock_data.json"
    
    registry = ToolRegistry(str(tools_path))
    executor = ToolExecutor(registry, str(mock_data_path))
    
    result = executor.execute("get_invoice", {"invoice_id": "INV-001"})
    
    assert isinstance(result, dict)
    assert result["id"] == "INV-001"


def test_approve_invoice():
    """Test approving an invoice."""
    tools_path = Path(__file__).parent.parent.parent.parent / "data" / "tools.json"
    mock_data_path = Path(__file__).parent.parent.parent.parent / "data" / "mock_data.json"
    
    registry = ToolRegistry(str(tools_path))
    executor = ToolExecutor(registry, str(mock_data_path))
    
    result = executor.execute("approve_invoice", {
        "invoice_id": "INV-001",
        "approver_id": "test_approver"
    })
    
    assert isinstance(result, dict)
    assert result["success"] is True


def test_execute_nonexistent_tool():
    """Test that executing a nonexistent tool raises error."""
    tools_path = Path(__file__).parent.parent.parent.parent / "data" / "tools.json"
    mock_data_path = Path(__file__).parent.parent.parent.parent / "data" / "mock_data.json"
    
    registry = ToolRegistry(str(tools_path))
    executor = ToolExecutor(registry, str(mock_data_path))
    
    with pytest.raises(ValueError, match="Tool not found"):
        executor.execute("nonexistent_tool", {})


def test_execute_with_invalid_arguments():
    """Test that executing with invalid arguments raises error."""
    tools_path = Path(__file__).parent.parent.parent.parent / "data" / "tools.json"
    mock_data_path = Path(__file__).parent.parent.parent.parent / "data" / "mock_data.json"
    
    registry = ToolRegistry(str(tools_path))
    executor = ToolExecutor(registry, str(mock_data_path))
    
    # get_invoice requires invoice_id
    with pytest.raises(ValueError):
        executor.execute("get_invoice", {})
