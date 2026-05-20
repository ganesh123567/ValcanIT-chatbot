# ValcanIT Chatbot Infrastructure

This folder keeps deployment concerns separate from the FastAPI application code.

## What It Runs

- `api`: FastAPI chatbot container
- `ollama`: Ollama container with persisted model storage

The API talks to Ollama through Docker networking:

```text
OLLAMA_BASE_URL=http://ollama:11434
```

## EC2 Prerequisites

Use an EC2 instance with enough RAM for the selected model. For `llama3.1:8b`, start with at least 8 GB RAM; more is better. CPU-only works but responses can be slow. A GPU instance improves latency.

Security group minimum:

- SSH: `22` from your IP
- API: `8000` from your IP for testing, or from your load balancer/reverse proxy for production
- Do not expose Ollama port `11434` publicly

## Deploy On EC2

1. Install Docker:

   ```bash
   ./infra/ec2/install_docker.sh
   ```

2. Log out and back in, or run:

   ```bash
   newgrp docker
   ```

3. Create the EC2 env file:

   ```bash
   cp infra/env/ec2.env.example infra/env/ec2.env
   ```

4. Update `infra/env/ec2.env`, especially:

   ```env
   ALLOWED_ORIGINS=https://valcanit.com,https://www.valcanit.com
   ```

5. Deploy:

   ```bash
   ./infra/ec2/deploy.sh
   ```

6. Test:

   ```bash
   curl http://localhost:8000/health
   curl -X POST http://localhost:8000/api/chat \
     -H "Content-Type: application/json" \
     -d '{"message":"Founder of ValcanIT"}'
   ```

## Update Knowledge From Word Docs

Copy `.docx` files into:

```text
data/documents/
```

Then run ingestion inside the API container:

```bash
docker compose -f infra/docker/docker-compose.ec2.yml exec -T api python scripts/ingest_documents.py
./infra/ec2/restart.sh
```

The compose file mounts `./data` into the API container, so ingested knowledge remains on the EC2 filesystem.

## Logs

```bash
./infra/ec2/logs.sh
```

## WordPress Embed

After the EC2 API is reachable through a public HTTPS domain, add this to the WordPress footer:

```html
<script
  src="https://chat.valcanit.com/widget.js"
  data-api-url="https://chat.valcanit.com/api/chat"
  data-title="ValcanIT Assistant"
  defer>
</script>
```

Use a real HTTPS domain in production. Put Nginx, an AWS Application Load Balancer, or another reverse proxy in front of port `8000`.
