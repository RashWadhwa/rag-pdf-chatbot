from pydantic import BaseModel, Field


class DocumentSummary(BaseModel):
    filename: str
    size: int = Field(ge=0)
    modified_at: float


class DocumentListResponse(BaseModel):
    documents: list[DocumentSummary]
    count: int = Field(ge=0)


class DeleteDocumentResponse(BaseModel):
    filename: str
    message: str
    remaining_documents: int = Field(ge=0)
    chunks: int = Field(ge=0)


class RebuildIndexResponse(BaseModel):
    documents: int = Field(ge=0)
    pages: int = Field(ge=0)
    chunks: int = Field(ge=0)
    message: str


class ClearDocumentsResponse(BaseModel):
    deleted_documents: int = Field(ge=0)
    message: str
    