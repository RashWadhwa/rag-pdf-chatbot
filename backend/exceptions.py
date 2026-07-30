from fastapi import Request
from fastapi.responses import JSONResponse

from loguru import logger


class DocumentNotLoaded(Exception):
    pass


class VectorStoreNotInitialized(Exception):
    pass


class EmptyQuestionException(Exception):
    pass


async def document_exception_handler(
    request: Request,
    exc: DocumentNotLoaded
):

    logger.error(str(exc))

    return JSONResponse(
        status_code=400,
        content={
            "detail": str(exc)
        }
    )


async def vector_store_exception_handler(
    request: Request,
    exc: VectorStoreNotInitialized
):

    logger.error(str(exc))

    return JSONResponse(
        status_code=400,
        content={
            "detail": str(exc)
        }
    )


async def empty_question_handler(
    request: Request,
    exc: EmptyQuestionException
):

    return JSONResponse(
        status_code=400,
        content={
            "detail": str(exc)
        }
    )