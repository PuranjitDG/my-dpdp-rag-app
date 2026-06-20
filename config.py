"""Central configuration. Override any value with an environment variable."""
import os

# --- Vector store (ChromaDB) ---
CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "dpdp_act")

# --- Documents ---
DATA_DIR = os.getenv("DATA_DIR", "./data")          # put the DPDP Act PDF here
CHUNK_CHARS = int(os.getenv("CHUNK_CHARS", "1000"))  # ~target chunk size in characters
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))

# --- Retrieval ---
TOP_K = int(os.getenv("TOP_K", "4"))                 # passages fed to the model
# Chroma cosine "distance" (0 = identical). Above this, treat as "not in the document".
MAX_DISTANCE = float(os.getenv("MAX_DISTANCE", "1.15"))

# --- LLM (Ollama) ---
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "120"))
