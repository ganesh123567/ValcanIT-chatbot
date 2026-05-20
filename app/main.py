from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.config import ALLOWED_ORIGINS, OLLAMA_EMBED_MODEL, OLLAMA_MODEL
from app.knowledge import retrieve_context
from app.ollama_client import OllamaError, generate_answer


SYSTEM_INSTRUCTIONS = """You are the ValcanIT website assistant for prospective clients.
Answer using only the ValcanIT context provided below.
Keep answers concise, professional, and helpful.
If the context does not contain the answer, say that you do not have that detail on the website and suggest contacting ValcanIT at info@valcanit.com or (469)-306-2882.
Do not invent pricing, timelines, certifications, openings, guarantees, or private company details.
"""


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1500)


class ChatResponse(BaseModel):
    answer: str
    model: str
    sources: list[str] = Field(default_factory=list)


app = FastAPI(title="ValcanIT Chatbot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "model": OLLAMA_MODEL, "embedding_model": OLLAMA_EMBED_MODEL}


@app.get("/")
async def demo_page() -> FileResponse:
    return FileResponse(Path("static/demo.html"), media_type="text/html")


@app.get("/widget.js")
async def widget() -> FileResponse:
    return FileResponse(Path("static/widget.js"), media_type="application/javascript")


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    retrieval = await retrieve_context(request.message)
    if not retrieval.matched:
        return ChatResponse(
            answer="I do not have that detail in the ValcanIT knowledge base. Please contact ValcanIT at info@valcanit.com or (469)-306-2882.",
            model=OLLAMA_MODEL,
            sources=[],
        )

    prompt = f"""{SYSTEM_INSTRUCTIONS}

ValcanIT context:
{retrieval.context}

Client question:
{request.message}

Answer:
"""

    try:
        answer = await generate_answer(prompt)
    except OllamaError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return ChatResponse(answer=answer, model=OLLAMA_MODEL, sources=list(retrieval.sources))
