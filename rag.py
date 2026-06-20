"""RAG core: retrieve relevant DPDP passages from ChromaDB, then answer with Ollama.

answer(question) -> {answer, grounded, sources, model}
"""
import threading

import requests

import config
from ingest import get_collection

_pull_lock = threading.Lock()
_pull_started = False


def _background_pull():
    """Pull the model in the background so the user can retry shortly (no server restart)."""
    try:
        import ensure_model
        ensure_model.pull()
    except Exception:
        pass

SYSTEM_PROMPT = (
    "You are a helpful assistant that answers questions about India's Digital Personal Data "
    "Protection (DPDP) Act and Rules. Answer ONLY using the provided context. If the answer is "
    "not in the context, say you could not find it in the DPDP document and suggest rephrasing. "
    "Do not invent sections, numbers, dates, or penalties. Be concise and clear. "
    "End with the page number(s) you used. This is general information, not legal advice."
)

PROMPT_TEMPLATE = """Context from the DPDP document:
{context}

Question: {question}

Answer using only the context above."""

# Reuse one collection handle across requests
_collection = None


def collection():
    global _collection
    if _collection is None:
        _collection = get_collection(reset=False)
    return _collection


def retrieve(question: str, k: int = None):
    k = k or config.TOP_K
    res = collection().query(query_texts=[question], n_results=k)
    chunks = []
    for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        chunks.append({"text": doc, "source": meta.get("source"),
                       "page": meta.get("page"), "distance": float(dist)})
    return chunks


def build_context(chunks):
    return "\n\n---\n\n".join(
        f"[page {c['page']}] {c['text']}" for c in chunks
    )


def ask_ollama(system: str, prompt: str):
    """Call the local Ollama server. Returns (text, ok)."""
    try:
        r = requests.post(
            f"{config.OLLAMA_URL}/api/chat",
            json={
                "model": config.OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
                "options": {"temperature": 0.1},
            },
            timeout=config.OLLAMA_TIMEOUT,
        )
    except requests.exceptions.ConnectionError:
        return (f"(Could not reach Ollama at {config.OLLAMA_URL}. Is the Ollama container "
                f"running? Try: docker compose up, or `ollama serve` locally.)"), False
    except Exception as e:
        return (f"(Error contacting Ollama: {e})"), False

    # 404 from /api/chat means the model isn't pulled yet. Start a one-time background
    # pull and ask the user to retry — no restart needed.
    if r.status_code == 404:
        global _pull_started
        with _pull_lock:
            if not _pull_started:
                _pull_started = True
                threading.Thread(target=_background_pull, daemon=True).start()
        return (f"The local model '{config.OLLAMA_MODEL}' is still downloading. "
                f"Please ask your question again in a few minutes. "
                f"(Or run: docker compose exec ollama ollama pull {config.OLLAMA_MODEL})"), False

    try:
        r.raise_for_status()
        return r.json()["message"]["content"].strip(), True
    except Exception as e:
        return (f"(Ollama returned an error: {e})"), False


def answer(question: str):
    chunks = retrieve(question)
    best = chunks[0]["distance"] if chunks else 9.9

    # Grounding guardrail: if nothing is close enough, refuse instead of hallucinating.
    if not chunks or best > config.MAX_DISTANCE:
        return {
            "answer": "I could not find this in the DPDP document. Try rephrasing your question.",
            "grounded": False, "sources": [], "model": config.OLLAMA_MODEL,
        }

    prompt = PROMPT_TEMPLATE.format(context=build_context(chunks), question=question)
    text, ok = ask_ollama(SYSTEM_PROMPT, prompt)

    sources = [{"page": c["page"], "source": c["source"],
                "distance": round(c["distance"], 3),
                "snippet": (c["text"][:200] + "…") if len(c["text"]) > 200 else c["text"]}
               for c in chunks]
    return {"answer": text, "grounded": True, "sources": sources,
            "model": config.OLLAMA_MODEL, "ollama_ok": ok}
