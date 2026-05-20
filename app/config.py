import os

from dotenv import load_dotenv


load_dotenv()


def _csv_env(name: str, default: str) -> list[str]:
    return [value.strip() for value in os.getenv(name, default).split(",") if value.strip()]


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
OLLAMA_TIMEOUT_SECONDS = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "60"))
RAG_MIN_SIMILARITY = float(os.getenv("RAG_MIN_SIMILARITY", "0.35"))

ALLOWED_ORIGINS = _csv_env(
    "ALLOWED_ORIGINS",
    "https://valcanit.com,https://www.valcanit.com,http://localhost:8000,http://127.0.0.1:8000",
)

KNOWLEDGE_PATH = os.getenv("KNOWLEDGE_PATH", "data/valcanit_knowledge.json")
