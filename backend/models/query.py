# Query Models
from pydantic import BaseModel


class QueryRequest(BaseModel):

    question: str


class Source(BaseModel):

    source: str

    page: int | None = None

    chunk_id: int | None = None


class QueryResponse(BaseModel):

    answer: str

    sources: list[Source]