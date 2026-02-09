from fastapi import APIRouter, HTTPException, status
from prometheus_client import Counter, Histogram
from corex.tool_factory import tool_factory_hardened, ToolCreationError
from corex.api.schemas.tools import ToolCreateRequest
from pydantic import BaseModel

router = APIRouter()

# --- METRICS ---
TOOL_CREATION_TOTAL = Counter('tool_creation_total', 'Total tools created', ['status'])
TOOL_CREATION_LATENCY = Histogram('tool_creation_latency_seconds', 'Time spent creating tools')

class ToolResponse(BaseModel):
    id: str
    status: str
    link: str

@router.post(
    "/create", 
    response_model=ToolResponse, 
    status_code=status.HTTP_201_CREATED,
    tags=["tools"]
)
async def create_tool_endpoint(payload: ToolCreateRequest):
    """
    Secure Tool Creation Endpoint.
    Validates input schema, sanitizes code, and registers tool.
    """
    with TOOL_CREATION_LATENCY.time():
        try:
            tool_id = tool_factory_hardened.create_tool(payload)
            TOOL_CREATION_TOTAL.labels(status="success").inc()
            return {
                "id": tool_id,
                "status": "created",
                "link": f"/api/v1/tools/{tool_id}"
            }
        except ToolCreationError as e:
            TOOL_CREATION_TOTAL.labels(status="failure").inc()
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:
            TOOL_CREATION_TOTAL.labels(status="error").inc()
            raise HTTPException(status_code=400, detail=str(e))
