from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from corex.config import settings
from corex.api.routes import system, voice, execute, modules, memory
from corex.auth.router import auth_router


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="LUMEN v18.5 - Modular Evolutionary Core",
        version="18.5.0",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include Routers
    app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
    app.include_router(system.router, prefix="", tags=["system"])  # /health, /status
    app.include_router(
        voice.router, prefix=f"{settings.API_V1_STR}/voice", tags=["voice"]
    )
    app.include_router(
        execute.router, prefix=f"{settings.API_V1_STR}", tags=["execute"]
    )
    app.include_router(
        modules.router, prefix=f"{settings.API_V1_STR}/module", tags=["modules"]
    )
    app.include_router(
        memory.router, prefix=f"{settings.API_V1_STR}", tags=["memory"]
    )

    # Static Files
    app.mount("/static", StaticFiles(directory="static"), name="static")

    return app
