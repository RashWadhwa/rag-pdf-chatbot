from backend.core.pdf_loader import PDFLoaderService
from backend.core.splitter import TextSplitterService
from backend.core.vector_store import VectorStoreService


loader = PDFLoaderService()

splitter = TextSplitterService()

vector_store = VectorStoreService()

documents = loader.load(
    "backend/storage/uploads/recipes.pdf"
)

chunks = splitter.split_documents(
    documents
)

vector_store.create(chunks)

vector_store.save()

print("Index Saved")

