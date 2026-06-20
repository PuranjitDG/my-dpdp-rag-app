# DPDP Chatbot

A website-embeddable AI chatbot that answers questions about India's **Digital Personal Data
Protection (DPDP) Act** — strictly from your DPDP PDF, with page citations, and a refusal when the
answer isn't in the document. It runs **fully locally**: ChromaDB for retrieval and Ollama
(`qwen2.5:1.5b`) for answers, so no data ever leaves the machine.

```
PDF ─► chunks ─► ChromaDB (vector search) ─► top passages ─► Ollama qwen2.5:1.5b ─► grounded answer + page
```

## Quickstart

```bash
pip install -r requirements.txt
ollama pull qwen2.5:1.5b            # one-time, from https://ollama.com
python make_sample_pdf.py          # or drop the real DPDP Act PDF into data/
python ingest.py                   # PDF -> ChromaDB (downloads the embedding model once)
uvicorn app:app --reload           # then open http://localhost:8000
```

- `http://localhost:8000/` — full-page chat
- `http://localhost:8000/demo` — a sample website with the chat **bubble embedded**
- `http://localhost:8000/api/health` — status

## Run with Docker (app + Ollama together)

```bash
docker compose up --build      # then open http://localhost:8000
```

See **`DOCKER.md`** for details. This runs the API and Ollama as two linked containers.

## Embed it on any website (one line)

```html
<script src="https://YOUR_HOST/widget.js" data-api="https://YOUR_HOST"></script>
```

The widget renders inside a Shadow DOM (isolated styling) and calls the API (CORS-enabled).

## Files

| File | What it does |
|------|--------------|
| `ingest.py` | PDF → chunks → ChromaDB |
| `rag.py` | retrieve from ChromaDB + answer with Ollama (with grounding guard) |
| `app.py` | FastAPI server: `/api/chat`, `/api/health`, serves UI + widget |
| `config.py` | all settings (model, chunk size, thresholds) |
| `static/widget.js` | the embeddable website widget |
| `static/demo-site.html` | sample site showing the widget |
| `static/index.html` | full-page chat |
| `make_sample_pdf.py` | builds a sample DPDP PDF for testing |

## Learn it / present it

- **`BUILD_GUIDE.md`** — build it on your computer step by step, with the concepts explained.
- **`INTERVIEW_PREP.md`** — the pitch, concept cheat-sheet, likely Q&A, and a demo script.

> The included `data/DPDP_sample.pdf` is a plain-language educational summary (current to the DPDP
> Rules 2025), not the official text and not legal advice. Replace it with the official PDF and run
> `python ingest.py --reset`.
```
