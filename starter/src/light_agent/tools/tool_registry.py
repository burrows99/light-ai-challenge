"""Tool registry for loading and managing tool schemas."""

import json
from pathlib import Path
from typing import Dict, List

from light_agent.models.tool import Tool


class ToolRegistry:
    """Registry for loading and accessing tool definitions."""
    
    def __init__(self, tools_path: str):
        """Initialize the registry with a path to tools.json.
        
        Args:
            tools_path: Path to the tools.json file
        """
        self.tools_path = Path(tools_path)
        self._tools: Dict[str, Tool] = {}
        self._load_tools()
    
    def _load_tools(self) -> None:
        """Load tool definitions from the JSON file."""
        with open(self.tools_path, 'r') as f:
            data = json.load(f)
        
        # Handle both formats: {"tools": [...]} or [...]
        tools_data = data.get("tools", data) if isinstance(data, dict) else data
        
        for tool_data in tools_data:
            tool = Tool(**tool_data)
            self._tools[tool.name] = tool
    
    def list_tools(self) -> List[str]:
        """List all available tool names.
        
        Returns:
            List of tool names
        """
        return list(self._tools.keys())
    
    def get_tool(self, name: str) -> Tool:
        """Get a tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Tool object
            
        Raises:
            ValueError: If tool not found
        """
        if name not in self._tools:
            raise ValueError(f"Tool not found: {name}")
        return self._tools[name]
    
    def get_all_tools(self) -> List[Tool]:
        """Get all tools as a list.
        
        Returns:
            List of all Tool objects
        """
        return list(self._tools.values())
