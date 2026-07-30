"""
FastAPI dependency providers.
"""

from fastapi import Request

from backend.core.rag_service import RAGService
from backend.core.service_registry import ServiceRegistry
from backend.services.document_manager import (
    DocumentManagerService,
)


def get_registry(request: Request) -> ServiceRegistry:
    """Return the application service registry."""

    return request.app.state.services


def get_rag_service(request: Request) -> RAGService:
    """Return the singleton RAG service."""

    return get_registry(request).rag


def get_document_manager(
    request: Request,
) -> DocumentManagerService:
    """Return the singleton document manager."""

    return get_registry(request).document_manager





