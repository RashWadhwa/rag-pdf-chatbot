# Embedding Service

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from backend.config import get_settings
from backend.logger import logger


class EmbeddingService:

    def __init__(self):

        settings = get_settings()

        logger.info("Initializing Gemini Embeddings...")

        self.embedding_model = GoogleGenerativeAIEmbeddings(

            model=settings.EMBEDDING_MODEL,

            google_api_key=settings.GOOGLE_API_KEY

        )

    @property
    def model(self):
        return self.embedding_model
