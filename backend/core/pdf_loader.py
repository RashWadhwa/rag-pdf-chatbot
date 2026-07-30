"""
PDF Loader Service

Loads PDF documents using PyMuPDF.
"""

from pathlib import Path

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.documents import Document

from backend.logger import logger


class PDFLoaderService:
    """
    Service responsible for loading PDF documents.
    """

    def load(self, pdf_path: str) -> list[Document]:
        """
        Load a PDF and return LangChain Document objects.

        Parameters
        ----------
        pdf_path : str

        Returns
        -------
        list[Document]
        """

        path = Path(pdf_path)

        if not path.exists():
            raise FileNotFoundError(f"{pdf_path} does not exist.")

        logger.info(f"Loading PDF: {pdf_path}")

        loader = PyMuPDFLoader(str(path))

        documents = loader.load()

        logger.info(f"Loaded {len(documents)} pages.")

        return documents

    def combine_pages(
        self,
        documents: list[Document]
    ) -> str:
        """
        Combine every page into one string.
        """

        logger.info("Combining pages...")

        return "\n".join(
            doc.page_content
            for doc in documents
        )

    def load_text(self, pdf_path: str) -> str:
        """
        Convenience method.

        PDF -> text
        """

        docs = self.load(pdf_path)

        return self.combine_pages(docs)
    
