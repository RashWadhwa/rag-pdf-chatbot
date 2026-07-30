from fastapi import FastAPI

from app.core.container import rag_service


app = FastAPI(
    title="Production RAG API"
)



@app.get("/")
async def root():

    return {
        "status": "running"
    }



@app.post("/ask")
async def ask_question(
    question: str
):

    response = (
        await rag_service.ask(
            question
        )
    )

    return response
