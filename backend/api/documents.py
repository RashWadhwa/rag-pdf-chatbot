"""
Document-management endpoints.
"""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from backend.dependencies import get_document_manager
from backend.logger import logger
from backend.models.documents import (
    ClearDocumentsResponse,
    DeleteDocumentResponse,
    DocumentListResponse,
    RebuildIndexResponse,
)
from backend.services.document_manager import (
    DocumentManagerService,
)

router = APIRouter()


@router.get(
    "/",
    response_model=DocumentListResponse,
)
async def list_documents(
    manager: DocumentManagerService = Depends(
        get_document_manager
    ),
) -> DocumentListResponse:
    """List all uploaded PDFs."""

    documents = manager.list_documents()

    return DocumentListResponse(
        documents=documents,
        count=len(documents),
    )


@router.delete(
    "/{filename}",
    response_model=DeleteDocumentResponse,
)
async def delete_document(
    filename: str,
    manager: DocumentManagerService = Depends(
        get_document_manager
    ),
) -> DeleteDocumentResponse:
    """Delete a PDF and rebuild the remaining index."""

    try:
        result = manager.delete_document(filename)

        return DeleteDocumentResponse(**result)

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.exception("Document deletion failed.")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The document could not be deleted.",
        ) from exc


@router.post(
    "/rebuild",
    response_model=RebuildIndexResponse,
)
async def rebuild_index(
    manager: DocumentManagerService = Depends(
        get_document_manager
    ),
) -> RebuildIndexResponse:
    """Rebuild FAISS from all stored PDFs."""

    try:
        result = manager.rebuild_index()

        return RebuildIndexResponse(**result)

    except Exception as exc:
        logger.exception("Vector-index rebuild failed.")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The vector index could not be rebuilt.",
        ) from exc


@router.delete(
    "/",
    response_model=ClearDocumentsResponse,
)
async def clear_documents(
    manager: DocumentManagerService = Depends(
        get_document_manager
    ),
) -> ClearDocumentsResponse:
    """Delete every uploaded PDF and clear FAISS."""

    try:
        result = manager.clear_all()

        return ClearDocumentsResponse(**result)

    except Exception as exc:
        logger.exception("Clearing documents failed.")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The documents could not be cleared.",
        ) from exc
    