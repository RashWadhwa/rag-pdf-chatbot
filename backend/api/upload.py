"""
PDF upload endpoint.
"""

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)

from backend.dependencies import get_document_manager
from backend.logger import logger
from backend.models.upload import UploadResponse
from backend.services.document_manager import (
    DocumentManagerService,
)

router = APIRouter()


@router.post(
    "/",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_pdf(
    file: UploadFile = File(...),
    manager: DocumentManagerService = Depends(
        get_document_manager
    ),
) -> UploadResponse:
    """Upload and index one PDF document."""

    try:
        result = await manager.upload(file)

        return UploadResponse(**result)

    except FileExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.exception("Unexpected PDF upload failure.")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The PDF could not be processed.",
        ) from exc
    