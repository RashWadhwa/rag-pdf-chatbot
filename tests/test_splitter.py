from backend.core.pdf_loader import PDFLoaderService

from backend.core.splitter import TextSplitterService


loader = PDFLoaderService()

splitter = TextSplitterService()


docs = loader.load(
    "backend/storage/uploads/recipes.pdf"
)

split_docs = splitter.split_documents(
    docs
)

print(len(split_docs))

print(split_docs[0].metadata)

print(split_docs[0].page_content)
