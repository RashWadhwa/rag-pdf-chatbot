"""
Retriever service.
"""

from langchain_core.documents import Document

from backend.config import get_settings
from backend.core.vector_store import VectorStoreService
from backend.logger import logger


class RetrieverService:
    """Retrieve relevant document chunks from the shared vector store."""

    def __init__(
        self,
        vector_store_service: VectorStoreService,
    ) -> None:
        settings = get_settings()

        self.k = settings.RETRIEVAL_K
        self.vector_store_service = vector_store_service

    def retrieve(
        self,
        query: str,
    ) -> list[Document]:
        """Retrieve the most relevant document chunks."""

        if not query or not query.strip():
            raise ValueError("Question cannot be empty.")

        logger.info(f"Retrieving context for: {query}")

        documents = self.vector_store_service.similarity_search(
            query=query.strip(),
            k=self.k,
        )

        logger.info(f"Retrieved {len(documents)} chunks.")

        return documents

    @staticmethod
    def context_from_documents(
        documents: list[Document],
    ) -> str:
        """Build a source-aware context string for the LLM."""

        context_sections: list[str] = []

        for document in documents:
            filename = document.metadata.get(
                "document",
                document.metadata.get("source", "Unknown"),
            )

            page = document.metadata.get("page")

            if isinstance(page, int):
                display_page: int | str = page + 1
            else:
                display_page = "Unknown"

            context_sections.append(
                f"Source: {filename}\n"
                f"Page: {display_page}\n"
                f"Content:\n{document.page_content}"
            )

        return "\n\n---\n\n".join(context_sections)
    