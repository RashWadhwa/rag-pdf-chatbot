from backend.core.pdf_loader import PDFLoaderService


loader = PDFLoaderService()

docs = loader.load(
    "backend/storage/uploads/recipes.pdf"
)

print(len(docs))

text = loader.combine_pages(docs)

print(text[:500])
