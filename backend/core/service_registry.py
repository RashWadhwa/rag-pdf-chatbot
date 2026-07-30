"""
Central application service registry.
"""

from backend.core.embeddings import EmbeddingService
from backend.core.llm import LLMService
from backend.core.pdf_loader import PDFLoaderService
from backend.core.rag_service import RAGService
from backend.core.retriever import RetrieverService
from backend.core.splitter import TextSplitterService
from backend.core.vector_store import VectorStoreService
from backend.logger import logger
from backend.services.document_manager import (
    DocumentManagerService,
)


class ServiceRegistry:
    """Create and wire singleton service instances."""

    def __init__(self) -> None:
        logger.info("Initializing application services...")

        self.pdf_loader = PDFLoaderService()
        self.splitter = TextSplitterService()
        self.embeddings = EmbeddingService()

        self.vector_store = VectorStoreService(
            embedding_service=self.embeddings,
        )

        if self.vector_store.exists():
            try:
                self.vector_store.load()
            except Exception:
                logger.exception(
                    "The existing FAISS index could not be loaded."
                )

        self.retriever = RetrieverService(
            vector_store_service=self.vector_store,
        )

        self.llm = LLMService()

        self.rag = RAGService(
            retriever=self.retriever,
            llm_service=self.llm,
        )

        self.document_manager = DocumentManagerService(
            loader=self.pdf_loader,
            splitter=self.splitter,
            vector_store=self.vector_store,
        )

        logger.success("Application services initialized.")
        
