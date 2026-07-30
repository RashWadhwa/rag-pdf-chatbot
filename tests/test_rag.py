from backend.core.rag_service import RAGService

rag = RAGService()

response = rag.ask(

    "How do I make Green Curry?"

)

print()

print(response["answer"])

print()

print(response["sources"])