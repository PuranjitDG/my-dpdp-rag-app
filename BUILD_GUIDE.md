# BUILD GUIDE — DPDP Chatbot (ChromaDB + Ollama + qwen2.5:1.5b)

This guide builds a **website-embeddable DPDP compliance chatbot** that runs entirely on your
own machine: no API keys, no cloud, no data leaving your computer. That last point is the whole
joke and the whole strength — it's a privacy-law bot that is itself privacy-preserving.

You can either (a) run the project as shipped, or (b) type it out yourself following the steps.
For learning and for the interview, do (b) at least once.

---

## 0. The mental model (read this first — it's what interviewers probe)

The chatbot is a **RAG** system: *Retrieval-Augmented Generation*.

A small language model like `qwen2.5:1.5b` does not know the DPDP Act, and if you just ask it,
it will confidently make things up ("hallucinate"). RAG fixes this by giving the model the
relevant text *at question time*:

```
  Your PDF ─► [INGEST, done once]                [ASK, every question]
            split into chunks                     question
                 │                                   │
              embed each chunk                    embed question
                 │                                   │
                 ▼                                   ▼
            ┌──────────────── ChromaDB (vector database) ────────────────┐
            │  stores chunk vectors; finds the chunks whose vectors are  │
            │  closest to the question vector  (semantic search)         │
            └────────────────────────────┬───────────────────────────────┘
                                         │ top 4 relevant chunks
                                         ▼
                       build a prompt:  "Use ONLY this context: <chunks>.
                                         Question: <question>"
                                         │
                                         ▼
                        Ollama running qwen2.5:1.5b  ─► grounded answer + page numbers
```

Two ideas to be able to say out loud:

1. **Embedding** = turning text into a list of numbers (a *vector*) so that texts with similar
   *meaning* end up close together in space. "child under 18" and "minors below eighteen years"
   land near each other even though they share few words. That's why it beats keyword search.
2. **Vector database (ChromaDB)** = stores those vectors and, given a new vector, returns the
   nearest ones fast. It is the "retrieval" in RAG.

The model only ever sees text you handed it, so it can cite a page and it refuses when the
answer isn't there. **Grounding** is the safety property that matters for a compliance tool.

---

## 1. Install the prerequisites

### Python 3.10+
- Windows: install from python.org, tick "Add Python to PATH".
- Mac: `brew install python` · Linux: usually already there (`python3 --version`).

### Ollama (the local LLM runtime)
1. Download from https://ollama.com and install.
2. Pull the model you'll use for answering:
   ```bash
   ollama pull qwen2.5:1.5b
   ```
3. Ollama runs a local server at `http://localhost:11434`. Test it:
   ```bash
   ollama run qwen2.5:1.5b "Say hello in one line"
   ```
   If that prints a reply, your LLM half is ready.

> Why qwen2.5:1.5b? It's tiny (~1 GB), fast on a laptop with no GPU, and good enough because
> **RAG does the heavy lifting** — the model only has to read the passages you give it and
> summarise. You can swap to `qwen2.5:3b` or `llama3.2:3b` later by changing one line.

---

## 2. Set up the project

```bash
mkdir dpdp-chatbot && cd dpdp-chatbot
python -m venv .venv
# activate it:
#   Windows: .venv\Scripts\activate
#   Mac/Linux: source .venv/bin/activate
pip install fastapi "uvicorn[standard]" chromadb pypdf requests reportlab
```

A **virtual environment** (`.venv`) keeps these libraries isolated to this project. Always
activate it before running anything.

Create this folder layout (the shipped zip already has it):

```
dpdp-chatbot/
├── config.py          # all settings in one place
├── ingest.py          # PDF -> chunks -> ChromaDB
├── rag.py             # retrieve + ask Ollama
├── app.py             # FastAPI web server
├── make_sample_pdf.py # optional: builds a test PDF
├── data/              # put the DPDP Act PDF here
└── static/            # web UI + embeddable widget
    ├── index.html
    ├── widget.js
    └── demo-site.html
```

---

## 3. Add the DPDP PDF

Put your DPDP Act / Rules PDF into the `data/` folder. Any filename ending in `.pdf` is picked
up. If you don't have it yet, generate a sample to test with:

```bash
python make_sample_pdf.py     # writes data/DPDP_sample.pdf
```

> Tip: you can keep multiple PDFs in `data/` (e.g. the Act *and* the Rules) — they all get
> indexed together, and each answer cites the page it used.

---

## 4. Build the vector database (ingest)

```bash
python ingest.py
```

What happens, step by step (this is `ingest.py`, worth reading line by line):

1. **Read the PDF** with `pypdf`, page by page (`extract_pages`). We keep the page number — it
   becomes the citation later.
2. **Chunk** each page into ~1000-character pieces with 150 chars of overlap (`chunk_text`).
   - *Why chunk?* You can't stuff a whole Act into a tiny model's context, and retrieval is
     sharper on small focused passages.
   - *Why overlap?* So a sentence sitting on a chunk boundary is still findable from both sides.
3. **Embed + store** in ChromaDB (`get_collection` + `collection.add`). The first run downloads
   the embedding model `all-MiniLM-L6-v2` (~80 MB) once; after that it's offline. The vectors
   persist on disk in `./chroma_db`, so you only ingest when the PDF changes.

You'll see `Done. Collection 'dpdp_act' now holds N chunks`. Re-run with `python ingest.py
--reset` to wipe and rebuild.

---

## 5. Start Ollama, then the chatbot

In one terminal, make sure Ollama is up (the desktop app does this; or run `ollama serve`).
In your project terminal:

```bash
uvicorn app:app --reload
```

Open the three things this exposes:

- **http://localhost:8000/** — full-page chat (best for testing).
- **http://localhost:8000/demo** — a fake company website with the chat **bubble embedded**.
- **http://localhost:8000/api/health** — JSON status (chunk count, model name).

Ask: *"What rights do I have over my personal data?"* You should get an answer that ends with a
page number, drawn only from your PDF.

---

## 6. How a question flows through the code (trace it once)

`app.py` `POST /api/chat` → `rag.answer(question)`:

1. `retrieve(question)` → ChromaDB embeds the question and returns the `TOP_K` closest chunks,
   each with a `distance` (smaller = more similar; ChromaDB cosine distance runs 0–2).
2. **Grounding check**: if the best `distance` is worse than `MAX_DISTANCE`, return a polite
   "couldn't find it" — *do not* call the model. This is the anti-hallucination guard.
3. Otherwise build the prompt (`PROMPT_TEMPLATE`) = the chunks + the question, with a strict
   `SYSTEM_PROMPT` ("answer ONLY from context, cite the page, don't invent").
4. `ask_ollama(...)` POSTs to `http://localhost:11434/api/chat` and returns qwen's reply.
5. Return `{answer, grounded, sources:[{page, snippet, distance}], model}`.

### Calibrating `MAX_DISTANCE`
Run a couple of real questions and a deliberately unrelated one ("how do I bake bread"), look at
the `distance` of the top source in `/api/health`-style output or by printing in `rag.retrieve`,
and set `MAX_DISTANCE` just below where the junk starts. With MiniLM, relevant hits are often
~0.4–0.8 and unrelated ~1.0+. It's in `config.py`.

---

## 7. Embedding the chatbot into a website (the deliverable)

This is the part that makes it "a website chatbot," and it's the headline feature.

`static/widget.js` is a **self-contained script**. Any website adds the bot with **one line**:

```html
<script src="https://YOUR_HOST/widget.js" data-api="https://YOUR_HOST"></script>
```

- `data-api` tells the widget where the chatbot API lives. On the same site you can leave it
  empty and it uses the current origin (that's what `/demo` does).
- The widget builds a floating bubble + chat panel inside a **Shadow DOM**. Shadow DOM is an
  isolated mini-document, so the host website's CSS can't break the widget and the widget's CSS
  can't leak out. This is how real embeddable chat widgets (Intercom, Drift) avoid style clashes
  — a strong thing to mention in the interview.
- The browser calls your API from another domain, which is why `app.py` enables **CORS**
  (`CORSMiddleware`). For production, change `allow_origins=["*"]` to your real site domains.

See it live at `/demo`. View the page source: the whole bot is that one `<script>` line.

---

## 8. Deploying so a real website can use it

The widget is just a static file, but the **API must run somewhere reachable**, and the API
needs **Ollama next to it**. Options, easiest first:

1. **Your own VPS** (DigitalOcean / Hetzner / a Hostinger VPS plan — *not* shared hosting, which
   can't run Python servers or Ollama). Steps: install Python + Ollama on the box, copy the
   project, `ollama pull qwen2.5:1.5b`, run `uvicorn app:app --host 0.0.0.0 --port 8000` behind
   Nginx with HTTPS. Point `data-api` at your domain.
2. **A container** (Docker) on any host that gives you CPU + a few GB RAM. Run Ollama as a second
   container and set `OLLAMA_URL` to its address.
3. **Demo / interview**: just run it locally and screen-share — no deployment needed.

> Reality check for the interview: a 1.5B model needs CPU and ~2–3 GB RAM but no GPU, which is
> exactly why this stack is cheap to self-host. If you needed higher answer quality you'd move to
> a bigger model or a hosted LLM and keep the same RAG code — say that and you sound senior.

---

## 9. Swapping the sample PDF for the real Act

1. Delete `data/DPDP_sample.pdf`, drop in the official DPDP Act (and Rules) PDF.
2. `python ingest.py --reset`
3. Restart `uvicorn`. Done — the bot now answers from the real text, citing real pages.

---

## 10. Common issues

- **"Could not reach Ollama"** in answers → Ollama isn't running or the model isn't pulled.
  Run `ollama serve` and `ollama pull qwen2.5:1.5b`.
- **First ingest is slow / fails offline** → it's downloading the MiniLM embedding model once.
  Be online for the first `python ingest.py`.
- **Bot refuses everything** → `MAX_DISTANCE` too strict, or the PDF had no extractable text
  (scanned image PDF). For scanned PDFs you'd add OCR (e.g. `ocrmypdf`) before ingesting.
- **Widget doesn't appear on another site** → check the browser console for a CORS error and
  confirm `data-api` points at the running API.
