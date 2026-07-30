from backend.core.vector_store import VectorStoreService

vector = VectorStoreService()

vector.load()

results = vector.similarity_search(

    "Green Curry",

    k=3

)

for doc in results:

    print("-" * 50)

    print(doc.metadata)

    print(doc.page_content[:250])
    