"""
Main retrieval-augmented generation service.
"""

from pathlib import Path
from typing import Any

from backend.core.llm import LLMService
from backend.core.prompt import PROMPT
from backend.core.retriever import RetrieverService
from backend.logger import logger


class RAGService:
    """Orchestrate retrieval, prompt construction, and answer generation."""

    def __init__(
        self,
        retriever: RetrieverService,
        llm_service: LLMService,
    ) -> None:
        self.retriever = retriever
        self.llm_service = llm_service
        self.chain = PROMPT | llm_service.model

    def ask(self, question: str) -> dict[str, Any]:
        """Answer a question using retrieved PDF context."""

        cleaned_question = question.strip()

        if not cleaned_question:
            raise ValueError("Question cannot be empty.")

        logger.info(f"RAG question: {cleaned_question}")

        documents = self.retriever.retrieve(cleaned_question)

        context = self.retriever.context_from_documents(documents)

        response = self.chain.invoke(
            {
                "context": context,
                "question": cleaned_question,
            }
        )

        sources: list[dict[str, Any]] = []
        seen_sources: set[tuple[str, Any, Any]] = set()

        for document in documents:
            raw_source = str(
                document.metadata.get(
                    "document",
                    document.metadata.get("source", "Unknown"),
                )
            )

            source = Path(raw_source).name
            stored_page = document.metadata.get("page")
            chunk_id = document.metadata.get("chunk_id")

            # PyMuPDF page metadata is normally zero-based.
            display_page = (
                stored_page + 1
                if isinstance(stored_page, int)
                else None
            )

            identity = (source, display_page, chunk_id)

            if identity in seen_sources:
                continue

            seen_sources.add(identity)

            sources.append(
                {
                    "source": source,
                    "page": display_page,
                    "chunk_id": chunk_id,
                }
            )

        logger.success("RAG answer generated.")

        return {
            "answer": response.content,
            "sources": sources,
            "context": context,
        }
        
