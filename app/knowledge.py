from __future__ import annotations

import asyncio
import json
import math
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.config import KNOWLEDGE_PATH, RAG_MIN_SIMILARITY
from app.ollama_client import OllamaError, generate_embeddings


_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "can",
    "do",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "me",
    "of",
    "on",
    "or",
    "our",
    "the",
    "their",
    "to",
    "us",
    "we",
    "what",
    "who",
    "with",
    "you",
    "your",
}


@dataclass(frozen=True)
class KnowledgeChunk:
    title: str
    content: str
    keywords: frozenset[str]
    title_keywords: frozenset[str]

    @property
    def prompt_text(self) -> str:
        return f"{self.title}: {self.content}"


@dataclass(frozen=True)
class RetrievalResult:
    context: str
    matched: bool
    sources: tuple[str, ...]


_EMBEDDING_LOCK = asyncio.Lock()
_EMBEDDING_CACHE: tuple[tuple[KnowledgeChunk, list[float]], ...] | None = None


def _tokens(text: str) -> set[str]:
    return {token for token in _TOKEN_RE.findall(text.lower()) if token not in _STOP_WORDS}


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0
    return dot / (left_norm * right_norm)


@lru_cache
def load_knowledge() -> tuple[KnowledgeChunk, ...]:
    path = Path(KNOWLEDGE_PATH)
    with path.open(encoding="utf-8") as file:
        items = json.load(file)

    chunks: list[KnowledgeChunk] = []
    for item in items:
        title = item["title"].strip()
        content = item["content"].strip()
        title_keywords = _tokens(title)
        keywords = _tokens(f"{title} {content} {' '.join(item.get('keywords', []))}")
        chunks.append(
            KnowledgeChunk(
                title=title,
                content=content,
                keywords=frozenset(keywords),
                title_keywords=frozenset(title_keywords),
            )
        )
    return tuple(chunks)


async def _knowledge_embeddings() -> tuple[tuple[KnowledgeChunk, list[float]], ...]:
    global _EMBEDDING_CACHE

    if _EMBEDDING_CACHE is not None:
        return _EMBEDDING_CACHE

    async with _EMBEDDING_LOCK:
        if _EMBEDDING_CACHE is not None:
            return _EMBEDDING_CACHE

        chunks = load_knowledge()
        embeddings = await generate_embeddings([chunk.prompt_text for chunk in chunks])
        _EMBEDDING_CACHE = tuple(zip(chunks, embeddings))
        return _EMBEDDING_CACHE


def _keyword_context(question: str, limit: int = 5) -> RetrievalResult:
    question_tokens = _tokens(question)
    if not question_tokens:
        selected: list[KnowledgeChunk] = []
    else:
        def score(chunk: KnowledgeChunk) -> int:
            title_matches = len(question_tokens & chunk.title_keywords)
            keyword_matches = len(question_tokens & chunk.keywords)
            return title_matches * 3 + keyword_matches

        scored = sorted(
            load_knowledge(),
            key=score,
            reverse=True,
        )
        selected = [chunk for chunk in scored if score(chunk) > 0][:limit]

    return RetrievalResult(
        context="\n\n".join(chunk.prompt_text for chunk in selected),
        matched=bool(selected),
        sources=tuple(chunk.title for chunk in selected),
    )


def _is_named_fact_question(question: str) -> bool:
    return bool(_named_fact_terms(question))


def _named_fact_terms(question: str) -> set[str]:
    tokens = _tokens(question)
    return tokens & _leadership_terms()


def _leadership_terms() -> set[str]:
    return {"ceo", "founder", "head", "owner", "president", "director", "leader", "leadership"}


async def retrieve_context(question: str, limit: int = 5) -> RetrievalResult:
    keyword_result = _keyword_context(question, limit)
    named_terms = _named_fact_terms(question)

    # For leadership/person questions, require an explicit leadership-related fact
    # in the knowledge base. This avoids answering from generic company text.
    if named_terms:
        leadership_chunks = [
            chunk
            for chunk in load_knowledge()
            if _leadership_terms() & chunk.keywords or _leadership_terms() & chunk.title_keywords
        ]
        if not leadership_chunks:
            return RetrievalResult(context="", matched=False, sources=())
        return RetrievalResult(
            context="\n\n".join(chunk.prompt_text for chunk in leadership_chunks[:limit]),
            matched=True,
            sources=tuple(chunk.title for chunk in leadership_chunks[:limit]),
        )

    try:
        question_embedding = (await generate_embeddings([question]))[0]
        scored = sorted(
            (
                (_cosine_similarity(question_embedding, embedding), chunk)
                for chunk, embedding in await _knowledge_embeddings()
            ),
            key=lambda item: item[0],
            reverse=True,
        )
    except OllamaError:
        return keyword_result

    selected = [chunk for score, chunk in scored if score >= RAG_MIN_SIMILARITY][:limit]
    if keyword_result.matched:
        keyword_chunks = [
            chunk
            for title in keyword_result.sources
            for chunk in load_knowledge()
            if chunk.title == title
        ]
        merged: list[KnowledgeChunk] = []
        for title in reversed(keyword_result.sources):
            chunk = next((item for item in load_knowledge() if item.title == title), None)
            if chunk and chunk.title not in {item.title for item in merged}:
                merged.insert(0, chunk)
        for chunk in selected:
            if chunk.title not in {item.title for item in merged}:
                merged.append(chunk)
        selected = (keyword_chunks + [chunk for chunk in merged if chunk.title not in keyword_result.sources])[:limit]

    return RetrievalResult(
        context="\n\n".join(chunk.prompt_text for chunk in selected),
        matched=bool(selected),
        sources=tuple(chunk.title for chunk in selected),
    )
