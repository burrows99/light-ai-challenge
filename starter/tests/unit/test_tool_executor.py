"""Unit tests for Tool Executor (Light AI's MockToolExecutor)."""

from pathlib import Path

from light_agent.mock_tools import MockToolExecutor
from light_agent.types import ToolCallStatus


def test_list_pending_invoices():
    """Test listing pending invoices."""
    mock_data_path = Path(__file__).parent.parent.parent.parent / "data" / "mock_data.json"
    
    executor = MockToolExecutor(str(mock_data_path))
    
    result = executor.execute("list_invoices", {"status": "pending"})
    
    assert result.status == ToolCallStatus.SUCCESS
    assert isinstance(result.result, list)
    assert len(result.result) > 0
    # All returned invoices should have pending status
    for invoice in result.result:
        assert invoice["status"] == "pending"


def test_get_specific_invoice():
    """Test getting a specific invoice by ID."""
    mock_data_path = Path(__file__).parent.parent.parent.parent / "data" / "mock_data.json"
    
    executor = MockToolExecutor(str(mock_data_path))
    
    result = executor.execute("get_invoice", {"invoice_id": "INV-001"})
    
    assert result.status == ToolCallStatus.SUCCESS
    assert isinstance(result.result, dict)
    assert result.result["id"] == "INV-001"


def test_approve_invoice():
    """Test approving an invoice."""
    mock_data_path = Path(__file__).parent.parent.parent.parent / "data" / "mock_data.json"
    
    executor = MockToolExecutor(str(mock_data_path))
    
    result = executor.execute("approve_invoice", {"invoice_id": "INV-001"})
    
    assert result.status == ToolCallStatus.SUCCESS
    assert isinstance(result.result, dict)
    assert result.result["success"] is True
    assert result.result["invoice_id"] == "INV-001"


def test_execute_nonexistent_tool():
    """Test executing a tool that doesn't exist."""
    mock_data_path = Path(__file__).parent.parent.parent.parent / "data" / "mock_data.json"
    
    executor = MockToolExecutor(str(mock_data_path))
    
    # Light AI's MockToolExecutor returns ERROR status instead of raising
    result = executor.execute("nonexistent_tool", {})
    assert result.status == ToolCallStatus.ERROR
    assert "unknown tool" in result.error.lower()


def test_execute_with_invalid_arguments():
    """Test that executing with invalid arguments returns error."""
    mock_data_path = Path(__file__).parent.parent.parent.parent / "data" / "mock_data.json"
    
    executor = MockToolExecutor(str(mock_data_path))
    
    # Light AI's MockToolExecutor handles missing invoice_id gracefully
    result = executor.execute("approve_invoice", {})
    # Will return error for not finding None or empty invoice
    assert result.status == ToolCallStatus.ERROR
