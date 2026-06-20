# ---- DPDP chatbot API (FastAPI + ChromaDB) ----
FROM python:3.12-slim

WORKDIR /app

# build-essential: in case any dependency needs to compile a wheel
# libgomp1: required by onnxruntime (used by ChromaDB's embedding model)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the embedding model (all-MiniLM-L6-v2) into the image so that
# ingest and query work without hitting the network at runtime.
RUN python -c "from chromadb.utils import embedding_functions as ef; ef.DefaultEmbeddingFunction()(['warmup'])"

COPY . .

EXPOSE 8000
ENTRYPOINT ["sh", "/app/docker-entrypoint.sh"]
