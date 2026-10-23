from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    auth,
    demo,
    evaluation,
    export,
    extract,
    health,
    interviews,
    rubrics,
    sessions,
    transcribe,
)
from app.config import get_settings
from app.db.base import create_all


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_all()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    for module in (
        health,
        auth,
        rubrics,
        interviews,
        transcribe,
        extract,
        sessions,
        evaluation,
        export,
        demo,
    ):
        app.include_router(module.router, prefix="/api")

    return app


app = create_app()
