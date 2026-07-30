from langchain_google_genai import ChatGoogleGenerativeAI

from backend.config import get_settings


class LLMService:

    def __init__(self):

        settings = get_settings()

        self.llm = ChatGoogleGenerativeAI(

            model=settings.LLM_MODEL,

            google_api_key=settings.GOOGLE_API_KEY,

            temperature=0.2

        )

    @property
    def model(self):

        return self.llm
    
