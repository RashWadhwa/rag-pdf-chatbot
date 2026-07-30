from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorStore
from app.services.retriever import Retriever
from app.services.prompt_builder import PromptBuilder
from app.services.llm import LLMService
from app.services.rag_service import RAGService



embedding_service = EmbeddingService()


vector_store = VectorStore()



retriever = Retriever(
    vector_store=vector_store,
    embedding_service=embedding_service
)



prompt_builder = PromptBuilder()


llm_service = LLMService()



rag_service = RAGService(
    retriever=retriever,
    llm_service=llm_service,
    prompt_builder=prompt_builder
)