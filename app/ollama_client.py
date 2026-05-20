from __future__ import annotations

import httpx

from app.config import OLLAMA_BASE_URL, OLLAMA_EMBED_MODEL, OLLAMA_MODEL, OLLAMA_TIMEOUT_SECONDS


class OllamaError(RuntimeError):
    pass


async def generate_answer(prompt: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "top_p": 0.9,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT_SECONDS) as client:
            response = await client.post(f"{OLLAMA_BASE_URL.rstrip('/')}/api/generate", json=payload)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise OllamaError("Ollama is not available or returned an error.") from exc

    data = response.json()
    answer = data.get("response", "").strip()
    if not answer:
        raise OllamaError("Ollama returned an empty response.")
    return answer


async def generate_embeddings(texts: list[str]) -> list[list[float]]:
    payload = {
        "model": OLLAMA_EMBED_MODEL,
        "input": texts,
    }

    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT_SECONDS) as client:
            response = await client.post(f"{OLLAMA_BASE_URL.rstrip('/')}/api/embed", json=payload)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise OllamaError("Ollama embedding model is not available or returned an error.") from exc

    data = response.json()
    embeddings = data.get("embeddings")
    if not isinstance(embeddings, list) or len(embeddings) != len(texts):
        raise OllamaError("Ollama returned invalid embeddings.")
    return embeddings
