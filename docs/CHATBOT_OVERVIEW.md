# ValcanIT Chatbot Overview

This document explains the current chatbot implementation, why each major part exists, and the advanced features planned for future versions.

## Goal

The chatbot helps ValcanIT website visitors ask questions about services, solutions, contact details, and verified company information.

The current version is intentionally simple:

- FastAPI backend
- Ollama local model integration
- RAG knowledge base
- JavaScript website widget
- Word document ingestion
- Swagger UI for API testing
- EC2 container deployment support

## Current Architecture

```text
ValcanIT Website / Local Demo
        |
        | loads widget.js
        v
Browser Chat Widget
        |
        | POST /api/chat
        v
FastAPI Backend
        |
        | retrieve matching context
        v
RAG Knowledge Base
        |
        | prompt + context
        v
Ollama Model
        |
        | generated answer
        v
FastAPI Response
        |
        v
Browser Chat Widget
```

## Main Components

### 1. Website Chat Widget

File:

```text
static/widget.js
```

Purpose:

- Creates the chat button and popup UI.
- Accepts user questions.
- Calls the backend API.
- Displays the chatbot answer.

The website only needs this script:

```html
<script
  src="https://YOUR-CHATBOT-DOMAIN.com/widget.js"
  data-api-url="https://YOUR-CHATBOT-DOMAIN.com/api/chat"
  data-title="ValcanIT Assistant"
  defer>
</script>
```

### 2. FastAPI Backend

File:

```text
app/main.py
```

Purpose:

- Defines the API endpoints.
- Serves the demo page and widget script.
- Receives chat requests.
- Calls the RAG retriever.
- Sends the final prompt to Ollama.
- Returns answers to the widget.

Current application endpoints:

```text
GET  /health
GET  /
GET  /widget.js
POST /api/chat
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

### 3. RAG Retrieval

File:

```text
app/knowledge.py
```

Purpose:

- Loads the ValcanIT knowledge base.
- Converts user questions and knowledge chunks into embeddings.
- Finds relevant chunks using semantic similarity.
- Uses keyword rules for direct matches.
- Prevents hallucination for sensitive facts like founder, CEO, head, owner, pricing, or leadership.

RAG means Retrieval-Augmented Generation. It does not train the model. It gives the model verified context at answer time.

Current RAG flow:

```text
User question
    |
    v
Keyword check
    |
    v
Embedding similarity search
    |
    v
Relevant knowledge chunks
    |
    v
Prompt sent to Ollama
```

### 4. Knowledge Base

File:

```text
data/valcanit_knowledge.json
```

Purpose:

- Stores verified business information used by the chatbot.
- Contains service descriptions, contact details, company overview, and ingested document chunks.

Example chunk:

```json
{
  "title": "Valcanit Leadership",
  "content": "ValcanIT founder is Vijay.",
  "keywords": ["valcanit", "leadership", "founder", "vijay"],
  "source_file": "data/documents/valcanit_leadership.docx"
}
```

### 5. Word Document Ingestion

File:

```text
scripts/ingest_documents.py
```

Purpose:

- Reads `.docx` files from `data/documents/`.
- Extracts text.
- Splits text into RAG chunks.
- Updates `data/valcanit_knowledge.json`.

Workflow:

```text
Add Word document
    |
    v
Run scripts/ingest_documents.py
    |
    v
Knowledge JSON updated
    |
    v
Restart FastAPI
    |
    v
Chatbot can answer from new content
```

Command:

```bash
.venv/bin/python scripts/ingest_documents.py
```

### 6. Ollama Client

File:

```text
app/ollama_client.py
```

Purpose:

- Calls Ollama `/api/embed` to generate embeddings.
- Calls Ollama `/api/generate` to generate final chatbot answers.

Models:

```text
OLLAMA_MODEL=llama3.1
OLLAMA_EMBED_MODEL=nomic-embed-text
```

### 7. Configuration

Files:

```text
.env
.env.example
infra/env/ec2.env.example
```

Purpose:

- Keeps environment-specific values outside the code.
- Local development uses `.env`.
- EC2 deployment uses `infra/env/ec2.env`.
- Example files are committed; real env files are ignored.

Important local value:

```env
OLLAMA_BASE_URL=http://localhost:11434
```

Important EC2 Docker value:

```env
OLLAMA_BASE_URL=http://ollama:11434
```

### 8. Logging

Files:

```text
app/logging_config.py
app/main.py
```

Purpose:

- Logs each HTTP request.
- Logs method, path, status code, duration, and client IP.
- Logs chat request flow, retrieved sources, Ollama errors, and answer length.

Example:

```text
request method=POST path=/api/chat status=200 duration_ms=2450.12 client=127.0.0.1
chat_context sources=1 titles=['Valcanit Leadership']
```

## Current Request Flow

```text
1. User opens website.
2. Browser loads /widget.js.
3. User asks a question.
4. Widget sends POST /api/chat.
5. FastAPI validates the request.
6. RAG retrieves matching ValcanIT context.
7. If no trusted context exists, API returns a safe fallback.
8. If context exists, FastAPI builds a prompt.
9. Ollama generates an answer.
10. API returns answer, model name, and source titles.
11. Widget displays the answer.
```

## Basic Version Capabilities

The current version supports:

- Website chatbot UI.
- FastAPI async backend.
- Ollama local LLM responses.
- RAG from JSON knowledge.
- RAG from Word documents after ingestion.
- Safe fallback for missing facts.
- Swagger UI for manual API testing.
- Request logging.
- EC2 container deployment using Docker Compose.

## Current Limitations

- No user authentication.
- No chat history persistence.
- No admin dashboard for uploading documents.
- No streaming responses yet.
- No analytics dashboard.
- No rate limiting.
- No production reverse proxy configuration included yet.
- No automated CI/CD pipeline yet.
- RAG data is stored in JSON instead of a vector database.

## Advanced Features Roadmap

For a dedicated plan for LangChain, FAISS, and vector database upgrades, see:

```text
docs/LANGCHAIN_FAISS_NEXT_VERSION.md
```

### Phase 1: Production Hardening

- Add Nginx or AWS Application Load Balancer in front of FastAPI.
- Add HTTPS with ACM or Certbot.
- Add rate limiting per IP.
- Add structured JSON logs.
- Add Docker health checks.
- Add `/ready` endpoint that verifies Ollama is reachable.

### Phase 2: Better User Experience

- Add streaming responses so users see tokens immediately.
- Add typing indicator based on streaming state.
- Add suggested questions.
- Add conversation memory per browser session.
- Add feedback buttons for answers.

### Phase 3: Better RAG

- Replace JSON-only retrieval with a vector database.
- Candidate options:
  - Chroma
  - Qdrant
  - PostgreSQL with pgvector
  - OpenSearch vector search
- Add source citations in the UI.
- Add document chunk preview for debugging.
- Add confidence scores.
- Add automatic re-ingestion when documents change.

### Phase 4: Admin Features

- Admin UI to upload Word/PDF documents.
- Admin UI to edit knowledge chunks.
- Admin UI to re-run ingestion.
- Admin-only API key authentication.
- Audit trail for knowledge changes.

### Phase 5: Observability

- Add request metrics.
- Track latency by endpoint.
- Track model response time.
- Track top questions.
- Track unanswered questions.
- Export logs to CloudWatch on AWS.

### Phase 6: CI/CD

- GitHub Actions workflow.
- Build Docker image on push.
- Push image to Amazon ECR.
- Deploy to EC2 or ECS.
- Run tests before deployment.

### Phase 7: AWS-Native Deployment

- Move from EC2 Docker Compose to ECS Fargate or ECS on EC2.
- Store env values in AWS Systems Manager Parameter Store.
- Store secrets in AWS Secrets Manager.
- Put CloudFront or ALB in front of the service.
- Add autoscaling.

## Recommended Next Technical Step

The best next improvement is streaming responses.

Why:

- Ollama can take several seconds to answer.
- Streaming makes the chatbot feel faster.
- Users see progress immediately.

After that, add:

1. Rate limiting.
2. CloudWatch logs.
3. Nginx or ALB with HTTPS.
4. Vector database for scalable RAG.
