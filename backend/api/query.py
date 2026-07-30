"""
RAG query endpoint.
"""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from backend.core.rag_service import RAGService
from backend.dependencies import get_rag_service
from backend.logger import logger
from backend.models.query import QueryRequest, QueryResponse

router = APIRouter()


@router.post(
    "/",
    response_model=QueryResponse,
)
async def ask_question(
    request: QueryRequest,
    rag: RAGService = Depends(get_rag_service),
) -> QueryResponse:
    """Answer a question using indexed PDF documents."""

    try:
        result = rag.ask(request.question)

        return QueryResponse(
            answer=result["answer"],
            sources=result["sources"],
        )

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "No vector index is available. "
                "Upload a PDF before asking questions."
            ),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.exception("RAG query failed.")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The question could not be answered.",
        ) from exc
    