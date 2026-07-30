"""
FastAPI application entry point.
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.router import api_router
from backend.config import get_settings
from backend.core.service_registry import ServiceRegistry
from backend.logger import logger

settings = get_settings()

@asynccontextmanager
async def lifespan(
    app: FastAPI,
) -> AsyncIterator[None]:
    """Initialize and clean up application services."""

    logger.info("Starting RAG application...")

    app.state.services = ServiceRegistry()

    logger.success("RAG application is ready.")

    yield

    logger.info("RAG application is shutting down.")

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=(
        "FastAPI backend for uploading and querying multiple PDFs "
        "using Gemini and FAISS."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/")
async def root() -> dict[str, str]:
    return {
        "status": "running",
        "message": "RAG backend is running.",
        "documentation": "/docs",
    }
