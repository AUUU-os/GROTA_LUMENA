from fastapi import APIRouter, Depends
from typing import Dict, List
from .schemas import (
    SwarmTask,
    AgentResponse,
    SwarmStatus,
    SwarmHealthResponse,
    ModelHealthInfo,
    TaskResult,
)
from .engine import swarm_engine
from .smart_router import smart_router, ROUTING_TABLE

# Import auth system from dedicated module to avoid circular import
from corex.auth import verify_token

router = APIRouter(prefix="/api/v1/swarm", tags=["Swarm Nexus"])


@router.get("/agents", response_model=List[str])
async def list_agents(token: str = Depends(verify_token)):
    """List all available local neural agents."""
    return await swarm_engine.list_agents()


@router.post("/task", response_model=AgentResponse)
async def dispatch_task(task: SwarmTask, token: str = Depends(verify_token)):
    """
    Dispatch a task to the local Swarm.
    Secured by OAuth2/Token via verify_token dependency.
    """
    response = await swarm_engine.execute_task(task)
    return response


@router.get("/routes")
async def get_routes(token: str = Depends(verify_token)) -> Dict[str, dict]:
    """Routing table z informacja o dostepnosci modeli."""
    available = await swarm_engine.list_agents()
    models = available if available != ["offline"] else None
    return smart_router.get_available_routes(models)


@router.post("/smart-task", response_model=AgentResponse)
async def smart_dispatch(task: SwarmTask, token: str = Depends(verify_token)):
    """Dispatch task z automatycznym smart routingiem.

    Jesli model_preference podane — override. Jesli nie — Smart Router dobiera model.
    """
    return await swarm_engine.execute_task(task)


@router.get("/health", response_model=SwarmHealthResponse)
async def swarm_health_detail(token: str = Depends(verify_token)):
    """Per-model health check z response time i routing info."""
    ollama_online = await swarm_engine.ping_ollama()
    agents = await swarm_engine.list_agents()
    is_online = agents != ["offline"]

    # Build reverse map: model -> task_types
    model_to_types: Dict[str, List[str]] = {}
    for task_type, config in ROUTING_TABLE.items():
        model_base = config["model"].split(":")[0]
        model_to_types.setdefault(model_base, []).append(task_type)

    models_info: List[ModelHealthInfo] = []
    if is_online:
        for model_name in agents:
            model_base = model_name.split(":")[0]
            routed = model_to_types.get(model_base, [])
            models_info.append(
                ModelHealthInfo(
                    name=model_name,
                    available=True,
                    routed_task_types=routed,
                )
            )

    return SwarmHealthResponse(
        ollama_online=ollama_online,
        models=models_info,
        total_models=len(models_info),
        task_history_size=len(swarm_engine._task_history),
        queue_size=swarm_engine.queue_size,
    )


@router.get("/history", response_model=List[TaskResult])
async def task_history(limit: int = 20, token: str = Depends(verify_token)):
    """Ostatnie wykonane zadania z wynikami routingu."""
    return swarm_engine.get_task_history(limit=min(limit, 100))


@router.get("/status", response_model=SwarmStatus)
async def swarm_status(token: str = Depends(verify_token)):
    """Check the heartbeat of the Swarm."""
    agents = await swarm_engine.list_agents()
    return SwarmStatus(
        active_agents=agents,
        gpu_status="ONLINE (RTX 2070 SUPER)",
        queue_size=swarm_engine.queue_size,
    )
