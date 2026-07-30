from langchain_core.prompts import PromptTemplate

PROMPT = PromptTemplate(

    input_variables=[

        "context",

        "question"

    ],

    template="""
You are an expert assistant.

Answer ONLY using the supplied context.

If the answer cannot be found in the context,
reply with:

"I don't know."

Context:

{context}

Question:

{question}

Answer:
"""
)
