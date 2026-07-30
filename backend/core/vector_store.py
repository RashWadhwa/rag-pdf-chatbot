"""
Persistent FAISS vector-store service.
"""

import shutil
from pathlib import Path
from threading import RLock

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from backend.config import get_settings
from backend.core.embeddings import EmbeddingService
from backend.logger import logger


class VectorStoreService:
    """Create, update, load, save, search, and clear a FAISS index."""

    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
    ) -> None:
        settings = get_settings()

        self.index_path = Path(settings.VECTOR_DB)
        self.embedding_service = (
            embedding_service or EmbeddingService()
        )
        self.embedding = self.embedding_service.model
        self.vector_store: FAISS | None = None
        self._lock = RLock()

    def exists(self) -> bool:
        """Return whether a complete persisted FAISS index exists."""

        return (
            (self.index_path / "index.faiss").is_file()
            and (self.index_path / "index.pkl").is_file()
        )

    def is_initialized(self) -> bool:
        """Return whether an index is currently loaded in memory."""

        return self.vector_store is not None

    def create(
        self,
        documents: list[Document],
    ) -> FAISS:
        """Create a new FAISS index from documents."""

        if not documents:
            raise ValueError(
                "Cannot create a vector store without documents."
            )

        with self._lock:
            logger.info(
                f"Creating FAISS index from {len(documents)} chunks..."
            )

            self.vector_store = FAISS.from_documents(
                documents=documents,
                embedding=self.embedding,
            )

            logger.success("FAISS index created.")

            return self.vector_store

    def add_documents(
        self,
        documents: list[Document],
    ) -> list[str]:
        """Append documents to the in-memory FAISS index."""

        if not documents:
            return []

        with self._lock:
            if self.vector_store is None:
                self.create(documents)
                return []

            logger.info(
                f"Adding {len(documents)} chunks to FAISS..."
            )

            document_ids = self.vector_store.add_documents(documents)

            logger.success("New chunks added to FAISS.")

            return document_ids

    def save(self) -> None:
        """Persist the current FAISS index to disk."""

        with self._lock:
            if self.vector_store is None:
                raise RuntimeError(
                    "Cannot save an uninitialized vector store."
                )

            self.index_path.mkdir(parents=True, exist_ok=True)

            self.vector_store.save_local(str(self.index_path))

            logger.success(
                f"FAISS index saved to {self.index_path}."
            )

    def load(self) -> FAISS:
        """Load a persisted FAISS index."""

        with self._lock:
            if not self.exists():
                raise FileNotFoundError(
                    f"No FAISS index exists at {self.index_path}."
                )

            logger.info(
                f"Loading FAISS index from {self.index_path}..."
            )

            self.vector_store = FAISS.load_local(
                folder_path=str(self.index_path),
                embeddings=self.embedding,
                allow_dangerous_deserialization=True,
            )

            logger.success("FAISS index loaded.")

            return self.vector_store

    def ensure_loaded(self) -> FAISS:
        """Return the in-memory index, loading it when necessary."""

        if self.vector_store is not None:
            return self.vector_store

        return self.load()

    def similarity_search(
        self,
        query: str,
        k: int = 3,
    ) -> list[Document]:
        """Run similarity search against the current index."""

        if not query or not query.strip():
            raise ValueError("Search query cannot be empty.")

        vector_store = self.ensure_loaded()

        return vector_store.similarity_search(
            query=query.strip(),
            k=k,
        )

    def clear(self) -> None:
        """Remove the in-memory and persisted FAISS index."""

        with self._lock:
            self.vector_store = None

            if self.index_path.exists():
                shutil.rmtree(self.index_path)

            logger.warning("FAISS index cleared.")

            
