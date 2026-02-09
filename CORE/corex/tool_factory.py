import uuid
import os
import json
import logging
import time
from typing import Dict
from corex.api.schemas.tools import ToolCreateRequest
from corex.logger import setup_logging

# Initialize Structured Logger
logger = logging.getLogger("corex.tool_factory")

class ToolCreationError(Exception):
    """Custom exception for tool creation failures"""
    pass

class ToolRegistry:
    def __init__(self, tools_dir: str = "modules/dynamic_tools"):
        self.tools_dir = tools_dir
        os.makedirs(self.tools_dir, exist_ok=True)
        self._ensure_init()

    def _ensure_init(self):
        init_path = os.path.join(self.tools_dir, "__init__.py")
        if not os.path.exists(init_path):
            with open(init_path, "w") as f:
                f.write('"""Dynamic Tools Registry v2.1"""')

    def create_tool(self, request: ToolCreateRequest) -> str:
        start_time = time.time()
        tool_id = self._generate_id(request.tool_name)
        
        try:
            # Security Scan (Basic)
            if "import os" in request.code_content or "import sys" in request.code_content:
                logger.warning(f"Potential risky import in tool {request.tool_name}", extra={"tool_id": tool_id})

            file_path = os.path.join(self.tools_dir, f"{tool_id}.py")
            metadata = {
                "id": tool_id,
                "name": request.tool_name,
                "created_at": time.time(),
                "schema": request.dict(exclude={"code_content"})
            }

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f'"""\nMETADATA: {json.dumps(metadata, default=str)}\n"""\n\n')
                f.write(request.code_content)

            duration = time.time() - start_time
            logger.info("Tool created successfully", extra={
                "tool_id": tool_id,
                "duration_ms": duration * 1000,
                "tool_name": request.tool_name
            })
            
            return tool_id

        except Exception as e:
            logger.error("Failed to create tool", extra={"error": str(e), "tool_name": request.tool_name})
            raise ToolCreationError(f"FileSystem Error: {str(e)}")

    def _generate_id(self, name: str) -> str:
        safe_name = name.lower().replace(" ", "_")
        return f"tool_{safe_name}_{uuid.uuid4().hex[:8]}"

tool_factory_hardened = ToolRegistry()
