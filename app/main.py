from __future__ import annotations

import logging
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.config import ALLOWED_ORIGINS, OLLAMA_EMBED_MODEL, OLLAMA_MODEL
from app.knowledge import retrieve_context
from app.logging_config import configure_logging
from app.ollama_client import OllamaError, generate_answer


configure_logging()
logger = logging.getLogger("valcanit_chatbot.api")

SYSTEM_INSTRUCTIONS = """You are the ValcanIT website assistant for prospective clients.
Answer using only the ValcanIT context provided below.
Keep answers concise, professional, and helpful.
If the context does not contain the answer, say that you do not have that detail on the website and suggest contacting ValcanIT at info@valcanit.com or (469)-306-2882.
Do not invent pricing, timelines, certifications, openings, guarantees, or private company details.
"""


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=1500,
        description="Client question to answer using the ValcanIT RAG knowledge base.",
        examples=["What services does ValcanIT provide?"],
    )


class ChatResponse(BaseModel):
    answer: str = Field(description="Chatbot answer returned to the website widget.")
    model: str = Field(description="Ollama generation model used for the response.")
    sources: list[str] = Field(default_factory=list, description="RAG source chunk titles used for the answer.")


app = FastAPI(
    title="ValcanIT Chatbot API",
    version="1.0.0",
    description="Backend API for the ValcanIT website chatbot using FastAPI, Ollama, and RAG.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "System", "description": "Health and operational endpoints."},
        {"name": "Chat", "description": "Client-facing chatbot endpoints."},
        {"name": "Frontend", "description": "Browser assets used by the website widget and local demo page."},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.perf_counter()
    response = None
    try:
        response = await call_next(request)
        return response
    finally:
        duration_ms = (time.perf_counter() - start_time) * 1000
        status_code = response.status_code if response else 500
        client_host = request.client.host if request.client else "unknown"
        logger.info(
            "request method=%s path=%s status=%s duration_ms=%.2f client=%s",
            request.method,
            request.url.path,
            status_code,
            duration_ms,
            client_host,
        )


@app.get(
    "/health",
    tags=["System"],
    summary="Check API health",
    description="Returns the API status and configured Ollama chat/embedding model names.",
)
async def health() -> dict[str, str]:
    return {"status": "ok", "model": OLLAMA_MODEL, "embedding_model": OLLAMA_EMBED_MODEL}


@app.get(
    "/",
    tags=["Frontend"],
    summary="Open local demo page",
    description="Serves a simple local page that loads the chatbot widget for testing.",
    include_in_schema=True,
)
async def demo_page() -> FileResponse:
    return FileResponse(Path("static/demo.html"), media_type="text/html")


@app.get(
    "/widget.js",
    tags=["Frontend"],
    summary="Load embeddable website widget",
    description="Serves the JavaScript widget that can be embedded on the ValcanIT website.",
)
async def widget() -> FileResponse:
    return FileResponse(Path("static/widget.js"), media_type="application/javascript")


@app.post(
    "/api/chat",
    response_model=ChatResponse,
    tags=["Chat"],
    summary="Ask the ValcanIT chatbot",
    description="Receives a client question, retrieves relevant RAG context, and asks Ollama to generate a grounded answer.",
)
async def chat(request: ChatRequest) -> ChatResponse:
    logger.info("chat_request message_length=%s", len(request.message))
    retrieval = await retrieve_context(request.message)
    if not retrieval.matched:
        logger.info("chat_no_context sources=0")
        return ChatResponse(
            answer="I do not have that detail in the ValcanIT knowledge base. Please contact ValcanIT at info@valcanit.com or (469)-306-2882.",
            model=OLLAMA_MODEL,
            sources=[],
        )

    logger.info("chat_context sources=%s titles=%s", len(retrieval.sources), list(retrieval.sources))

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
        logger.exception("chat_ollama_error")
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    logger.info("chat_response answer_length=%s", len(answer))
    return ChatResponse(answer=answer, model=OLLAMA_MODEL, sources=list(retrieval.sources))
