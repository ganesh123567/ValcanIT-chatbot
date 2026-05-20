# ValcanIT Ollama Chatbot

Small FastAPI service that exposes an Ollama-backed chatbot API and a JavaScript widget you can embed on `valcanit.com`.

For a detailed explanation of the current chatbot architecture, request flow, RAG behavior, and future roadmap, see:

```text
docs/CHATBOT_OVERVIEW.md
```

## Local setup

1. Install and start Ollama.
2. Pull a model:

   ```bash
   ollama pull llama3.1
   ollama pull nomic-embed-text
   ```

3. Install Python dependencies:

   ```bash
   .venv/bin/python -m pip install -r requirements.txt
   ```

4. Start the API:

   ```bash
   OLLAMA_MODEL=llama3.1 .venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. Test the API:

   ```bash
   curl -X POST http://localhost:8000/api/chat \
     -H "Content-Type: application/json" \
     -d '{"message":"What services does ValcanIT provide?"}'
   ```

## API Verification

The service currently exposes 4 application endpoints:

- `GET /health`: API health and configured model names
- `GET /`: local chatbot demo page
- `GET /widget.js`: embeddable website widget JavaScript
- `POST /api/chat`: chatbot question endpoint

Swagger UI is available at:

```text
http://127.0.0.1:8000/docs
```

ReDoc is available at:

```text
http://127.0.0.1:8000/redoc
```

OpenAPI JSON is available at:

```text
http://127.0.0.1:8000/openapi.json
```

## Website embed

After deploying this FastAPI app, add this script to the WordPress site footer:

```html
<script
  src="https://YOUR-CHATBOT-DOMAIN.com/widget.js"
  data-api-url="https://YOUR-CHATBOT-DOMAIN.com/api/chat"
  data-title="ValcanIT Assistant"
  defer>
</script>
```

Set `ALLOWED_ORIGINS` on the server to include the production website:

```bash
ALLOWED_ORIGINS=https://valcanit.com,https://www.valcanit.com
```

## Configuration

Runtime settings are loaded from `.env`. Keep `.env` private and use `.env.example` as the shareable template.

- `OLLAMA_BASE_URL`: Ollama server URL
- `OLLAMA_MODEL`: chat generation model
- `OLLAMA_EMBED_MODEL`: embedding model for RAG
- `OLLAMA_TIMEOUT_SECONDS`: Ollama request timeout
- `RAG_MIN_SIMILARITY`: minimum semantic similarity score for retrieved chunks
- `ALLOWED_ORIGINS`: comma-separated list of allowed browser origins
- `KNOWLEDGE_PATH`: RAG knowledge JSON path

Update `data/valcanit_knowledge.json` when services, contact details, or website content changes.
For facts like founder, CEO, head of company, leadership, prices, or hiring details, add a verified entry to the knowledge file first. The chatbot is configured to avoid inventing those answers when the fact is missing.

## EC2 Container Deployment

Infrastructure files for AWS EC2 container deployment live in `infra/`.

Start with:

```bash
cat infra/README.md
```

## Add RAG Facts

RAG does not train the model weights. It adds verified facts to the knowledge base that the model receives with each question.

Example:

```bash
.venv/bin/python scripts/add_fact.py \
  --title "Leadership" \
  --content "ValcanIT's founder is VERIFIED_NAME_HERE." \
  --keywords founder ceo head owner leadership
```

Then restart FastAPI:

```bash
.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Ingest Word Documents

You can also put `.docx` files in `data/documents/` and run:

```bash
.venv/bin/python scripts/ingest_documents.py
```

The script extracts document text, splits it into RAG chunks, and updates `data/valcanit_knowledge.json`. Restart FastAPI after ingestion.
