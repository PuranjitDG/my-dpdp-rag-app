"""FastAPI server for the DPDP chatbot.

Endpoints:
    POST /api/chat     -> {answer, grounded, sources, model}
    GET  /api/health   -> service + vector store status
    GET  /             -> full-page chat UI (for local testing)
    GET  /demo         -> a sample website with the widget embedded
    /widget.js, /static/* -> embeddable widget + assets

Run:  uvicorn app:app --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import config
import rag

app = FastAPI(title="DPDP Chatbot", version="1.0.0")

# Allow the widget to call this API from any website.
# In production, replace ["*"] with your specific site origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)


class ChatIn(BaseModel):
    message: str


@app.post("/api/chat")
def chat(body: ChatIn):
    return rag.answer(body.message)


@app.get("/api/health")
def health():
    try:
        n = rag.collection().count()
        vs = "ok"
    except Exception as e:
        n, vs = 0, f"error: {e}"
    return {"status": "ok", "vector_store": vs, "chunks": n,
            "model": config.OLLAMA_MODEL, "ollama_url": config.OLLAMA_URL}


@app.get("/")
def home():
    return FileResponse("static/index.html")


@app.get("/demo")
def demo():
    return FileResponse("static/demo-site.html")


@app.get("/widget.js")
def widget():
    return FileResponse("static/widget.js", media_type="application/javascript")


app.mount("/static", StaticFiles(directory="static"), name="static")
