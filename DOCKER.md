# Running with Docker

`docker compose` brings up **three services**:

- **`ollama`** — runs the official Ollama image with its default startup (`ollama serve`). We do
  **not** override it (overriding it is what caused the earlier "interactive menu / unhealthy" bug).
- **`model-pull`** — a one-shot helper that runs `ollama pull qwen2.5:1.5b` against the Ollama
  server and then exits. This is the compose equivalent of
  `docker compose exec ollama ollama pull qwen2.5:1.5b`, done for you automatically.
- **`app`** — FastAPI + ChromaDB + the embeddable widget. It waits for `model-pull` to finish, so
  by the time it serves, the model is already there. It reaches Ollama at `http://ollama:11434`.

```
            ┌──────────────── docker-compose network ────────────────┐
 browser ─► │  app (FastAPI, ChromaDB, widget) :8000                 │
            │    │ http://ollama:11434                                 │
            │    ▼                                                     │
            │  ollama (qwen2.5:1.5b) :11434  ◄── model-pull (one-shot) │
            └─────────────────────────────────────────────────────────┘
```

## Prerequisites
- Docker Desktop (Mac/Windows) or Docker Engine + Compose plugin (Linux).
- Put your DPDP Act PDF in `./data/` (a sample PDF is already there to test with).

## Start it

```bash
docker compose up --build
```

On the **first** run, in order: the app image builds (baking in the embedding model), `model-pull`
downloads `qwen2.5:1.5b` into the `ollama_models` volume (watch `dpdp-model-pull` logs for the %),
then the app builds the vector index and starts. Because the app waits for `model-pull` to
complete, the very first question already works — no 404.

On later runs the model is cached, so `model-pull` finishes instantly and the app starts quickly.

Open:
- http://localhost:8000/ — full-page chat
- http://localhost:8000/demo — the widget embedded on a sample site
- http://localhost:8000/api/health — status

Stop with `Ctrl+C`, or `docker compose down` (add `-v` to also delete the model + index volumes).

## Re-index after changing the PDF
```bash
docker compose exec app python ingest.py
```
(or `docker compose down -v && docker compose up` to wipe everything and start fresh.)

## What the pieces do
- `Dockerfile` — builds the app image; the `RUN python -c "...DefaultEmbeddingFunction..."` line
  bakes the embedding model in so runtime never needs the network for embeddings.
- `docker-compose.yml` — the three services above, the network, and volumes (`ollama_models`,
  `chroma_index`).
- `ensure_model.py` / `docker-entrypoint.sh` — a safety net inside the app: if the model still
  isn't present, it pulls it; otherwise it just builds the index (if needed) and starts uvicorn.
- The chat code also self-heals: if a question ever hits a missing model, it starts the download
  and asks you to retry shortly.

## Changing the model
Edit the model name in **two** places to keep them in sync:
- `model-pull` entrypoint in `docker-compose.yml` (`ollama pull <model>`)
- the `OLLAMA_MODEL` env var on the `app` service

## Troubleshooting

**`model-pull` fails to download.**
Usually a network blip pulling from the Ollama registry. Re-run `docker compose up` (it retries),
or pull manually: `docker compose exec ollama ollama pull qwen2.5:1.5b`. Confirm with
`docker compose exec ollama ollama list`.

**`OLLAMA_HOST` errors in the `model-pull` logs.**
Some Ollama versions want the host without a scheme. Change `http://ollama:11434` to `ollama:11434`
in the `model-pull` service.

**`container for service "ollama" is unhealthy` + an interactive menu in the logs.**
The Ollama container's startup was overridden so the bare `ollama` command ran. Make sure the
`ollama` service has **no** `entrypoint`/`command` lines (only `model-pull` overrides entrypoint,
and it always includes the `pull` subcommand).

**Bot refuses everything.**
`MAX_DISTANCE` in `config.py` is too strict, or the PDF is a scanned image with no extractable
text (add OCR before ingesting).

## Notes
- **CPU is fine.** `qwen2.5:1.5b` needs ~2–3 GB RAM, no GPU.
- **Production:** set CORS `allow_origins` in `app.py` to your real domain(s), put the app behind
  Nginx/Caddy with HTTPS, and point the widget's `data-api` at that URL.
