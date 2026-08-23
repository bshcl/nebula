#!/bin/sh
set -e

# Build Chroma index on first run when no persisted DB exists.
if [ ! -d "var/chroma_db" ] || [ -z "$(ls -A var/chroma_db 2>/dev/null)" ]; then
  echo "[entrypoint] Initializing RAG knowledge base..."
  python scripts/init_rag.py
fi

exec uvicorn main:app --host 0.0.0.0 --port 8000
