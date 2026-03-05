"""Tool executor for running tools with mock data."""

import json
from pathlib import Path
from typing import Any, Dict, List

from light_agent.tools.tool_registry import ToolRegistry


class ToolExecutor:
    """Executes tools using mock data backend."""
    
    def __init__(self, registry: ToolRegistry, mock_data_path: str):
        """Initialize the executor.
        
        Args:
            registry: ToolRegistry instance
            mock_data_path: Path to mock_data.json
        """
        self.registry = registry
        self.mock_data_path = Path(mock_data_path)
        self._mock_data = self._load_mock_data()
    
    def _load_mock_data(self) -> Dict[str, Any]:
        """Load mock data from JSON file."""
        with open(self.mock_data_path, 'r') as f:
            return json.load(f)
    
    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool with given arguments.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            
        Returns:
            Tool execution result
            
        Raises:
            ValueError: If tool not found or validation fails
        """
        # Get tool definition
        tool = self.registry.get_tool(tool_name)
        
        # Validate required parameters
        self._validate_arguments(tool, arguments)
        
        # Execute the tool based on its name
        if tool_name == "list_invoices":
            return self._list_invoices(arguments)
        elif tool_name == "get_invoice":
            return self._get_invoice(arguments)
        elif tool_name == "approve_invoice":
            return self._approve_invoice(arguments)
        elif tool_name == "reject_invoice":
            return self._reject_invoice(arguments)
        elif tool_name == "schedule_payment":
            return self._schedule_payment(arguments)
        else:
            raise ValueError(f"Tool implementation not found: {tool_name}")
    
    def _validate_arguments(self, tool: Any, arguments: Dict[str, Any]) -> None:
        """Validate that required arguments are provided.
        
        Args:
            tool: Tool definition
            arguments: Provided arguments
            
        Raises:
            ValueError: If required arguments are missing
        """
        required = tool.parameters.required if hasattr(tool.parameters, 'required') else []
        for param in required:
            if param not in arguments:
                raise ValueError(f"Missing required parameter: {param}")
    
    def _list_invoices(self, args: Dict[str, Any]) -> List[Dict[str, Any]]:
        """List invoices with optional filters."""
        invoices = self._mock_data.get("invoices", [])
        
        # Apply filters
        status = args.get("status", "all")
        if status != "all":
            invoices = [inv for inv in invoices if inv.get("status") == status]
        
        vendor = args.get("vendor")
        if vendor:
            invoices = [inv for inv in invoices 
                       if vendor.lower() in inv.get("vendor", "").lower()]
        
        min_amount = args.get("min_amount")
        if min_amount is not None:
            invoices = [inv for inv in invoices if inv.get("amount", 0) >= min_amount]
        
        max_amount = args.get("max_amount")
        if max_amount is not None:
            invoices = [inv for inv in invoices if inv.get("amount", 0) <= max_amount]
        
        currency = args.get("currency")
        if currency:
            invoices = [inv for inv in invoices if inv.get("currency") == currency]
        
        return invoices
    
    def _get_invoice(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get a specific invoice by ID."""
        invoice_id = args["invoice_id"]
        invoices = self._mock_data.get("invoices", [])
        
        for invoice in invoices:
            if invoice.get("id") == invoice_id:
                return invoice
        
        raise ValueError(f"Invoice not found: {invoice_id}")
    
    def _approve_invoice(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Approve an invoice (mock implementation)."""
        invoice_id = args["invoice_id"]
        approver_id = args["approver_id"]
        
        # Verify invoice exists
        self._get_invoice({"invoice_id": invoice_id})
        
        return {
            "success": True,
            "invoice_id": invoice_id,
            "approver_id": approver_id,
            "message": f"Invoice {invoice_id} approved by {approver_id}"
        }
    
    def _reject_invoice(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Reject an invoice (mock implementation)."""
        invoice_id = args["invoice_id"]
        rejector_id = args["rejector_id"]
        reason = args.get("reason", "No reason provided")
        
        # Verify invoice exists
        self._get_invoice({"invoice_id": invoice_id})
        
        return {
            "success": True,
            "invoice_id": invoice_id,
            "rejector_id": rejector_id,
            "reason": reason,
            "message": f"Invoice {invoice_id} rejected"
        }
    
    def _schedule_payment(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule a payment (mock implementation)."""
        invoice_id = args["invoice_id"]
        payment_date = args["payment_date"]
        
        # Verify invoice exists
        invoice = self._get_invoice({"invoice_id": invoice_id})
        
        return {
            "success": True,
            "invoice_id": invoice_id,
            "amount": invoice.get("amount"),
            "currency": invoice.get("currency"),
            "scheduled_date": payment_date,
            "message": f"Payment scheduled for {payment_date}"
        }
