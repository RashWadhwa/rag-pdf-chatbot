"""
Text chunking service.
"""

from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.config import get_settings
from backend.logger import logger


class TextSplitterService:
    """Split text and LangChain documents into retrieval chunks."""

    def __init__(self) -> None:
        settings = get_settings()

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=[
                "\n\n",
                "\n",
                ". ",
                " ",
                "",
            ],
        )

    def split_text(self, text: str) -> list[str]:
        """Split plain text into chunks."""

        if not text or not text.strip():
            return []

        logger.info("Splitting plain text...")

        chunks = self.splitter.split_text(text)

        logger.info(f"{len(chunks)} text chunks created.")

        return chunks

    def create_documents(
        self,
        chunks: list[str],
        source: str,
    ) -> list[Document]:
        """
        Convert plain-text chunks into LangChain Document objects.

        This method remains available for non-PDF text ingestion.
        """

        source_path = Path(source)
        documents: list[Document] = []

        for index, chunk in enumerate(chunks):
            if not chunk.strip():
                continue

            documents.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "chunk_id": index,
                        "source": str(source_path),
                        "document": source_path.name,
                    },
                )
            )

        logger.info(f"{len(documents)} Document objects created.")

        return documents

    def split_documents(
        self,
        documents: list[Document],
    ) -> list[Document]:
        """
        Split LangChain documents while preserving and enriching metadata.

        PyMuPDFLoader metadata, including source and page, is retained.
        """

        if not documents:
            return []

        logger.info("Splitting documents...")

        split_documents = self.splitter.split_documents(documents)

        for chunk_id, document in enumerate(split_documents):
            source = str(document.metadata.get("source", "Unknown"))

            document.metadata["source"] = source
            document.metadata["document"] = Path(source).name
            document.metadata["chunk_id"] = chunk_id

            # Some loaders may use page_number instead of page.
            if "page" not in document.metadata:
                document.metadata["page"] = document.metadata.get(
                    "page_number"
                )

        logger.info(f"{len(split_documents)} chunks generated.")

        return split_documents

    