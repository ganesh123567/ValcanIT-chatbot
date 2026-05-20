# LangChain + FAISS Next Version Plan

This document explains how the ValcanIT chatbot can evolve from the current simple RAG implementation into a LangChain + vector database architecture.

## Current RAG Version

The current chatbot uses:

- FastAPI for APIs
- Ollama for chat generation
- Ollama `nomic-embed-text` for embeddings
- JSON knowledge storage in `data/valcanit_knowledge.json`
- Word document ingestion through `scripts/ingest_documents.py`
- In-memory semantic retrieval in `app/knowledge.py`

Current flow:

```text
Word documents
    |
    v
scripts/ingest_documents.py
    |
    v
data/valcanit_knowledge.json
    |
    v
In-memory embeddings and retrieval
    |
    v
Ollama answer generation
```

This version is good for a basic chatbot and a small amount of knowledge.

## Why Move To LangChain + Vector DB

As the number of documents grows, the current JSON-based RAG will become harder to maintain.

Problems with the current version at larger scale:

- JSON is not ideal for many documents and chunks.
- Embedding cache is process-local.
- Retrieval logic is custom code.
- Source metadata is basic.
- Rebuilding and updating knowledge is manual.
- It is harder to support PDFs, TXT files, webpages, and future data sources.

LangChain and a vector DB solve many of these issues.

## Proposed Next Architecture

```text
data/documents/
    services.docx
    leadership.docx
    faq.pdf
    company_profile.txt
        |
        v
LangChain Document Loaders
        |
        v
Text Splitter
        |
        v
Ollama Embeddings
        |
        v
FAISS Vector Store
        |
        v
Retriever
        |
        v
Prompt Template
        |
        v
Ollama Chat Model
        |
        v
FastAPI /api/chat Response
```

## What LangChain Adds

LangChain gives reusable building blocks for RAG.

Useful LangChain parts:

- Document loaders for Word, PDF, text, websites, and more.
- Text splitters for chunking large documents.
- Embedding integrations.
- Vector store integrations.
- Retriever interfaces.
- Prompt templates.
- Chains for connecting retrieval and LLM calls.
- Conversation memory, if needed later.

Instead of maintaining all retrieval logic manually in `app/knowledge.py`, the next version can use LangChain retrievers and vector stores.

## What FAISS Adds

FAISS is a local vector index library from Meta. It stores embeddings and performs fast similarity search.

With FAISS, the chatbot can search document chunks like this:

```text
User question
    |
    v
Question embedding
    |
    v
FAISS similarity search
    |
    v
Top matching chunks
    |
    v
Ollama answer
```

## Advantages Of FAISS

### 1. Fast Similarity Search

FAISS is optimized for vector search. It is faster and more scalable than manually comparing every embedding in Python as the number of chunks grows.

### 2. Local And Private

FAISS runs locally inside the application environment.

Benefits:

- No external vector database service.
- No additional cloud cost.
- ValcanIT documents stay on the server.
- Simple EC2 deployment.

### 3. Works Well With Ollama

The chatbot can continue using:

```text
OLLAMA_EMBED_MODEL=nomic-embed-text
```

Those embeddings can be stored in FAISS and queried from FastAPI.

### 4. Persistent Index

FAISS indexes can be saved to disk:

```text
data/vectorstore/
    index.faiss
    index.pkl
```

After restarting FastAPI, the app can load the saved index instead of recomputing all embeddings.

### 5. Better Source Tracking

Each chunk can include metadata:

```json
{
  "source": "services.docx",
  "chunk": 3,
  "section": "Workday Solutions"
}
```

The API can return source citations in the response.

Example:

```json
{
  "answer": "ValcanIT provides Workday, SAP, Oracle, and integration solutions.",
  "sources": [
    {
      "file": "services.docx",
      "section": "Enterprise Solutions",
      "chunk": 3
    }
  ]
}
```

### 6. Simple EC2 Deployment

FAISS does not require another database container.

Current EC2 deployment:

```text
FastAPI container
Ollama container
```

Next version with FAISS:

```text
FastAPI container
    |
    v
data/vectorstore/

Ollama container
```

The infrastructure remains simple.

## FAISS Limitations

FAISS is powerful, but it is not a full database.

Limitations:

- No built-in authentication.
- No rich query language.
- Metadata filtering is limited compared with dedicated vector databases.
- Index updates need careful handling.
- Multiple API replicas need a shared or rebuilt index.
- Backups must include vector index files.

FAISS is still a good next step because the project currently targets a simple EC2 deployment.

## FAISS Compared With Other Vector Databases

| Option | Best For | Tradeoff |
| --- | --- | --- |
| FAISS | Simple local vector search | Not a full database |
| Chroma | Local development and prototypes | Less mature for production scale |
| Qdrant | Production vector search with metadata filtering | Requires another service/container |
| PostgreSQL + pgvector | Teams already using Postgres | Slower than specialized vector engines at high scale |
| OpenSearch | Enterprise search and hybrid keyword/vector search | Heavier setup and operations |

Recommended next version:

```text
LangChain + FAISS + Ollama embeddings
```

Reason:

- Keeps deployment simple.
- Improves retrieval quality.
- Avoids an extra database server.
- Supports future migration to Qdrant or pgvector.

## Proposed Folder Structure

```text
app/
  rag/
    __init__.py
    loaders.py
    splitter.py
    vector_store.py
    retriever.py
    prompts.py
    chain.py

scripts/
  build_vector_index.py

data/
  documents/
    leadership.docx
    services.docx
  vectorstore/
    index.faiss
    index.pkl
```

## Proposed Dependencies

```text
langchain
langchain-community
langchain-ollama
faiss-cpu
python-docx
pypdf
```

## Next Version Build Plan

### Phase 1: Add LangChain Dependencies

Update `requirements.txt`:

```text
langchain
langchain-community
langchain-ollama
faiss-cpu
pypdf
```

Keep `python-docx` because Word document ingestion is already supported.

### Phase 2: Build A Vector Index Script

Add:

```text
scripts/build_vector_index.py
```

Responsibilities:

- Load files from `data/documents/`.
- Support `.docx`, `.pdf`, and `.txt`.
- Split documents into chunks.
- Generate embeddings using Ollama.
- Store vectors in FAISS.
- Store metadata with each chunk.

Command:

```bash
.venv/bin/python scripts/build_vector_index.py
```

### Phase 3: Add RAG Modules

Add:

```text
app/rag/vector_store.py
app/rag/retriever.py
app/rag/prompts.py
app/rag/chain.py
```

Responsibilities:

- Load FAISS index.
- Retrieve top matching chunks.
- Build the final prompt.
- Call Ollama.
- Return answer and sources.

### Phase 4: Update `/api/chat`

Current:

```text
/api/chat -> app/knowledge.py -> Ollama
```

Next:

```text
/api/chat -> app/rag/retriever.py -> app/rag/chain.py -> Ollama
```

The response can include richer sources:

```json
{
  "answer": "Vijay is the founder of ValcanIT.",
  "model": "llama3.1",
  "sources": [
    {
      "file": "valcanit_leadership.docx",
      "chunk": 1
    }
  ]
}
```

### Phase 5: Update Infra

Persist FAISS files on EC2:

```text
data/vectorstore/
```

The existing Docker Compose data mount already supports this:

```text
../../data:/app/data
```

So vector index files can survive container rebuilds.

### Phase 6: Keep JSON As Fallback During Migration

For a safe transition, keep the existing JSON-based RAG temporarily.

Fallback strategy:

```text
If FAISS index exists:
    use LangChain + FAISS
else:
    use current JSON RAG
```

This avoids breaking local development or deployment if the vector index has not been built yet.

## Recommended API Changes

Current response:

```json
{
  "answer": "Vijay is the founder of ValcanIT.",
  "model": "llama3.1",
  "sources": ["Valcanit Leadership"]
}
```

Recommended next response:

```json
{
  "answer": "Vijay is the founder of ValcanIT.",
  "model": "llama3.1",
  "sources": [
    {
      "title": "Valcanit Leadership",
      "file": "valcanit_leadership.docx",
      "chunk": 1,
      "score": 0.82
    }
  ]
}
```

This will make debugging and client trust better.

## Recommended Priority

Recommended implementation order:

1. Add LangChain and FAISS dependencies.
2. Build `scripts/build_vector_index.py`.
3. Add `app/rag/` modules.
4. Keep current JSON RAG as fallback.
5. Return richer source metadata.
6. Add Swagger examples for source-rich responses.
7. Add EC2 deployment docs for rebuilding vector index.

## When To Move Beyond FAISS

Move from FAISS to Qdrant, pgvector, or OpenSearch if:

- Document volume grows very large.
- Multiple backend containers need to share the same vector index.
- You need strong metadata filtering.
- You need real-time document updates.
- You need user-specific document permissions.
- You need managed backups and observability for vectors.

Until then, FAISS is a strong next step for this project.
