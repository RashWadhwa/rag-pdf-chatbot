"""
Document manager service.

Orchestrates PDF storage, loading, chunking, indexing,
listing, deletion, rebuilding, and clearing.
"""

import re
from pathlib import Path
from threading import RLock
from typing import Any

from fastapi import UploadFile

from backend.config import get_settings
from backend.core.pdf_loader import PDFLoaderService
from backend.core.splitter import TextSplitterService
from backend.core.vector_store import VectorStoreService
from backend.logger import logger


class DocumentManagerService:
    """Manage the complete lifecycle of uploaded PDF documents."""

    def __init__(
        self,
        loader: PDFLoaderService,
        splitter: TextSplitterService,
        vector_store: VectorStoreService,
    ) -> None:
        self.settings = get_settings()
        self.loader = loader
        self.splitter = splitter
        self.vector_store = vector_store
        self.upload_folder = Path(self.settings.UPLOAD_FOLDER)
        self._lock = RLock()

        self.upload_folder.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _safe_filename(filename: str) -> str:
        """
        Remove path components and unsupported filename characters.

        This prevents directory traversal such as ../../file.pdf.
        """

        filename = Path(filename).name.strip()

        if not filename:
            raise ValueError("Filename cannot be empty.")

        sanitized = re.sub(
            r"[^A-Za-z0-9._ -]",
            "_",
            filename,
        )

        if not sanitized.lower().endswith(".pdf"):
            raise ValueError("Only PDF files are supported.")

        return sanitized

    async def _save_upload(
        self,
        upload: UploadFile,
        destination: Path,
    ) -> int:
        """Save an UploadFile incrementally and return its size."""

        bytes_written = 0
        chunk_size = 1024 * 1024

        try:
            with destination.open("wb") as output:
                while data := await upload.read(chunk_size):
                    output.write(data)
                    bytes_written += len(data)
        finally:
            await upload.close()

        if bytes_written == 0:
            destination.unlink(missing_ok=True)
            raise ValueError("The uploaded PDF is empty.")

        return bytes_written

    async def upload(
        self,
        file: UploadFile,
    ) -> dict[str, Any]:
        """Save, process, and incrementally index one PDF."""

        filename = self._safe_filename(file.filename or "")

        if (
            file.content_type
            and file.content_type
            not in {
                "application/pdf",
                "application/x-pdf",
                "application/octet-stream",
            }
        ):
            raise ValueError("Only PDF files are supported.")

        destination = self.upload_folder / filename

        with self._lock:
            if destination.exists():
                raise FileExistsError(
                    f"{filename} has already been uploaded."
                )

        logger.info(f"Saving uploaded document: {filename}")

        try:
            file_size = await self._save_upload(
                file,
                destination,
            )

            documents = self.loader.load(str(destination))

            if not documents:
                raise ValueError(
                    "No readable pages were found in the PDF."
                )

            chunks = self.splitter.split_documents(documents)

            if not chunks:
                raise ValueError(
                    "No searchable text was found in the PDF."
                )

            with self._lock:
                if self.vector_store.is_initialized():
                    self.vector_store.add_documents(chunks)
                elif self.vector_store.exists():
                    self.vector_store.load()
                    self.vector_store.add_documents(chunks)
                else:
                    self.vector_store.create(chunks)

                self.vector_store.save()

        except Exception:
            # Prevent a failed upload from remaining in the documents list.
            destination.unlink(missing_ok=True)
            logger.exception(
                f"Failed to process uploaded document: {filename}"
            )
            raise

        logger.success(f"Document indexed: {filename}")

        return {
            "filename": filename,
            "pages": len(documents),
            "chunks": len(chunks),
            "size": file_size,
            "message": "PDF uploaded and indexed successfully.",
        }

    def list_documents(self) -> list[dict[str, Any]]:
        """Return metadata for all stored PDFs."""

        documents: list[dict[str, Any]] = []

        for pdf_path in sorted(
            self.upload_folder.glob("*.pdf"),
            key=lambda path: path.name.lower(),
        ):
            stat = pdf_path.stat()

            documents.append(
                {
                    "filename": pdf_path.name,
                    "size": stat.st_size,
                    "modified_at": stat.st_mtime,
                }
            )

        return documents

    def delete_document(
        self,
        filename: str,
    ) -> dict[str, Any]:
        """
        Delete a PDF and rebuild the index from remaining PDFs.

        Rebuilding is necessary because FAISS does not provide a reliable
        filename-level deletion operation for this document store.
        """

        safe_filename = self._safe_filename(filename)
        destination = self.upload_folder / safe_filename

        with self._lock:
            if not destination.is_file():
                raise FileNotFoundError(
                    f"{safe_filename} was not found."
                )

            destination.unlink()

            rebuild_result = self.rebuild_index()

        logger.success(f"Deleted document: {safe_filename}")

        return {
            "filename": safe_filename,
            "message": "Document deleted successfully.",
            "remaining_documents": rebuild_result[
                "documents"
            ],
            "chunks": rebuild_result["chunks"],
        }

    def rebuild_index(self) -> dict[str, int | str]:
        """Recreate FAISS from every PDF currently in storage."""

        with self._lock:
            pdf_files = sorted(
                self.upload_folder.glob("*.pdf"),
                key=lambda path: path.name.lower(),
            )

            self.vector_store.clear()

            if not pdf_files:
                logger.info(
                    "No PDFs remain; vector index is empty."
                )

                return {
                    "documents": 0,
                    "pages": 0,
                    "chunks": 0,
                    "message": "No documents available to index.",
                }

            all_chunks = []
            total_pages = 0

            for pdf_path in pdf_files:
                logger.info(
                    f"Re-indexing {pdf_path.name}..."
                )

                documents = self.loader.load(str(pdf_path))
                chunks = self.splitter.split_documents(documents)

                total_pages += len(documents)
                all_chunks.extend(chunks)

            if not all_chunks:
                return {
                    "documents": len(pdf_files),
                    "pages": total_pages,
                    "chunks": 0,
                    "message": (
                        "Documents were found but contained no "
                        "searchable text."
                    ),
                }

            self.vector_store.create(all_chunks)
            self.vector_store.save()

            logger.success(
                f"Rebuilt index with {len(all_chunks)} chunks."
            )

            return {
                "documents": len(pdf_files),
                "pages": total_pages,
                "chunks": len(all_chunks),
                "message": "Vector index rebuilt successfully.",
            }

    def clear_all(self) -> dict[str, Any]:
        """Delete all uploaded PDFs and clear the FAISS index."""

        with self._lock:
            deleted_documents = 0

            for pdf_path in self.upload_folder.glob("*.pdf"):
                pdf_path.unlink()
                deleted_documents += 1

            self.vector_store.clear()

        logger.warning(
            f"Cleared {deleted_documents} documents and the index."
        )

        return {
            "deleted_documents": deleted_documents,
            "message": "All documents and vector data were cleared.",
        }