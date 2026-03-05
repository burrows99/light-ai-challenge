"""Mock LLM client for testing."""

from typing import Any, Dict, List


class MockLLMClient:
    """Mock LLM client that returns scripted responses."""
    
    def __init__(self):
        """Initialize mock LLM client."""
        self.call_count = 0
    
    def generate(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate a response based on conversation context.
        
        Args:
            messages: Conversation history
            tools: Available tools
            
        Returns:
            Response dict with type and relevant fields
        """
        self.call_count += 1
        
        # Get last user message
        user_message = self._get_last_user_message(messages)
        
        # Count tool results to track conversation progress
        tool_results = sum(1 for msg in messages if msg.get("role") == "tool")
        
        # Simple routing logic based on user message content
        if tool_results == 0:
            # First turn - decide whether to call a tool
            if self._should_call_tool(user_message, tools):
                return self._generate_tool_call(user_message, tools)
            else:
                return self._generate_final_answer(user_message)
        else:
            # After tool results - give final answer
            return self._generate_final_answer_from_results(messages)
    
    def _get_last_user_message(self, messages: List[Dict[str, str]]) -> str:
        """Extract the last user message."""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                return msg.get("content", "")
        return ""
    
    def _should_call_tool(self, user_message: str, tools: List[Dict[str, Any]]) -> bool:
        """Determine if we should call a tool."""
        keywords = ["list", "show", "get", "find", "approve", "reject", "schedule"]
        user_lower = user_message.lower()
        
        # Call tool if we have tools and message contains keywords
        return len(tools) > 0 and any(kw in user_lower for kw in keywords)
    
    def _generate_tool_call(
        self,
        user_message: str,
        tools: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate a tool call response."""
        user_lower = user_message.lower()
        
        # Simple keyword matching
        if "list" in user_lower or "show" in user_lower:
            tool_name = "list_invoices"
            arguments = {}
            
            if "pending" in user_lower:
                arguments["status"] = "pending"
            if "overdue" in user_lower:
                arguments["status"] = "overdue"
            if "unpaid" in user_lower:
                arguments["status"] = "pending"
            
            return {
                "type": "tool_call",
                "tool": tool_name,
                "arguments": arguments
            }
        
        elif "approve" in user_lower:
            # Extract invoice ID (very basic)
            return {
                "type": "tool_call",
                "tool": "approve_invoice",
                "arguments": {
                    "invoice_id": "INV-001",
                    "approver_id": "system"
                }
            }
        
        else:
            # Default to first available tool
            if tools:
                tool_name = tools[0].get("name", "list_invoices")
                return {
                    "type": "tool_call",
                    "tool": tool_name,
                    "arguments": {}
                }
        
        return {
            "type": "final_answer",
            "content": "I'm not sure how to help with that."
        }
    
    def _generate_final_answer(self, user_message: str) -> Dict[str, Any]:
        """Generate a final answer without tool use."""
        return {
            "type": "final_answer",
            "content": f"Based on your question about '{user_message}', here is my response."
        }
    
    def _generate_final_answer_from_results(
        self,
        messages: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Generate final answer after tool results."""
        return {
            "type": "final_answer",
            "content": "Based on the tool results, here is the answer to your question."
        }
