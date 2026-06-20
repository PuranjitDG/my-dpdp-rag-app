#!/bin/sh
set -e

# 1) Make sure the Ollama model is available (waits for Ollama, pulls if needed).
echo "[entrypoint] Ensuring Ollama model '${OLLAMA_MODEL:-qwen2.5:1.5b}' is available..."
python ensure_model.py || echo "[entrypoint] Model check skipped/failed; continuing."

# 2) Build the vector index on first run (when the volume is empty).
INDEX_DIR="${CHROMA_PATH:-./chroma_db}"
if [ -z "$(ls -A "$INDEX_DIR" 2>/dev/null)" ]; then
  echo "[entrypoint] No vector index found — building from PDFs in ${DATA_DIR:-./data} ..."
  python ingest.py || echo "[entrypoint] WARNING: ingest failed (is there a PDF in data/?)."
else
  echo "[entrypoint] Existing vector index found — skipping ingest."
fi

# 3) Start the API.
echo "[entrypoint] Starting API on :8000"
exec uvicorn app:app --host 0.0.0.0 --port 8000
