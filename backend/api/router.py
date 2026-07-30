from fastapi import APIRouter

from backend.api.documents import router as documents_router
from backend.api.health import router as health_router
from backend.api.query import router as query_router
from backend.api.upload import router as upload_router

api_router = APIRouter()

api_router.include_router(
    health_router,
    prefix="/health",
    tags=["Health"],
)

api_router.include_router(
    upload_router,
    prefix="/upload",
    tags=["Upload"],
)

api_router.include_router(
    documents_router,
    prefix="/documents",
    tags=["Documents"],
)

api_router.include_router(
    query_router,
    prefix="/query",
    tags=["Query"],
)