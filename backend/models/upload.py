from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    filename: str
    pages: int = Field(ge=0)
    chunks: int = Field(ge=0)
    size: int = Field(ge=0)
    message: str
    
