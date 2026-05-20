from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Add a verified fact to the ValcanIT RAG knowledge base.")
    parser.add_argument("--title", required=True, help="Short title, for example: Leadership")
    parser.add_argument("--content", required=True, help="Verified fact text the chatbot may use.")
    parser.add_argument("--keywords", nargs="+", default=[], help="Search terms, for example: founder ceo head leadership")
    parser.add_argument("--path", default="data/valcanit_knowledge.json", help="Knowledge JSON path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    path = Path(args.path)
    if path.exists():
        with path.open(encoding="utf-8") as file:
            knowledge = json.load(file)
    else:
        knowledge = []

    knowledge.append(
        {
            "title": args.title.strip(),
            "content": args.content.strip(),
            "keywords": [keyword.strip() for keyword in args.keywords if keyword.strip()],
        }
    )

    with path.open("w", encoding="utf-8") as file:
        json.dump(knowledge, file, indent=2)
        file.write("\n")

    print(f"Added fact to {path}: {args.title}")
    print("Restart the FastAPI server so the RAG cache reloads.")


if __name__ == "__main__":
    main()
