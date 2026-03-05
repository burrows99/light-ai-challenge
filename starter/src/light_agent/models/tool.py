"""Tool models and schemas."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ToolParameter(BaseModel):
    """Schema for tool parameter definition."""
    type: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    required: List[str] = Field(default_factory=list)


class ToolMetadata(BaseModel):
    """Metadata about tool execution characteristics."""
    mutating: bool = False
    requires_confirmation: bool = False
    irreversible: bool = False
    idempotent: bool = True


class Tool(BaseModel):
    """Complete tool definition."""
    name: str
    description: str
    parameters: ToolParameter
    metadata: ToolMetadata = Field(default_factory=ToolMetadata)
