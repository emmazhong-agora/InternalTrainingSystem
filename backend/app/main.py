from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.api_v1 import api_router
from app.core.config import get_settings
from app.dependencies.services import get_agora_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    agora_service = None
    try:
        if get_settings().agora_api_key:
            agora_service = get_agora_service()
        yield
    finally:
        if agora_service:
            await agora_service.aclose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.project_name, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/healthz")
    def healthcheck():
        return {"status": "ok"}

    return app


app = create_app()
