"""FastAPI app entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from bms_data_generator import __version__
from bms_data_generator.api.control import get_router as get_control_router
from bms_data_generator.api.datasets import get_router as get_datasets_router
from bms_data_generator.api.health import get_router as get_health_router
from bms_data_generator.api.query import get_router as get_query_router
from bms_data_generator.config import get_settings
from bms_data_generator.logging_config import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(level=settings.log_level)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="CAPTIA BMS Synthetic Data Generator",
        version=__version__,
        lifespan=lifespan,
    )
    origins = [o.strip() for o in settings.cors_allow_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(get_health_router())
    app.include_router(get_control_router())
    app.include_router(get_datasets_router())
    app.include_router(get_query_router())
    return app


app = create_app()
