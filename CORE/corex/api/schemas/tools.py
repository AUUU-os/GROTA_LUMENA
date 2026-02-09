from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, List, Optional
import re

class ToolParameterSchema(BaseModel):
    type: str = Field(..., pattern="^(string|integer|boolean|number|array|object)$")
    description: str
    required: bool = False

class ToolCreateRequest(BaseModel):
    tool_name: str = Field(..., min_length=3, max_length=50, description="Unique name of the tool")
    tool_description: str = Field(..., min_length=10, max_length=500)
    parameters: Dict[str, ToolParameterSchema] = Field(default_factory=dict)
    code_content: str = Field(..., min_length=20, description="Python code implementing 'execute(**kwargs)'")
    dependencies: List[str] = Field(default_factory=list)

    @field_validator('tool_name')
    def name_must_be_alphanumeric(cls, v):
        if not re.match(r'^[a-zA-Z0-9_\- ]+$', v):
            raise ValueError('Tool name must be alphanumeric')
        return v.strip()

    @field_validator('code_content')
    def code_must_contain_execute(cls, v):
        if "def execute(" not in v:
            raise ValueError("Code must contain a 'def execute(...)' function entry point.")
        return v
