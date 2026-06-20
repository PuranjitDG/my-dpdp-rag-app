"""Wait for the Ollama server to be ready and make sure the model is pulled.

Run automatically by the container entrypoint before the API starts. Safe to run anytime:
if the model is already present (cached in the ollama volume) it returns immediately.
"""
import json
import sys
import time

import requests

import config


def wait_for_server(timeout: int = 300) -> bool:
    """Poll Ollama's /api/tags until it responds (server is up)."""
    url = f"{config.OLLAMA_URL}/api/tags"
    start = time.time()
    while time.time() - start < timeout:
        try:
            requests.get(url, timeout=3).raise_for_status()
            return True
        except Exception:
            print("  waiting for Ollama server...", flush=True)
            time.sleep(2)
    return False


def has_model() -> bool:
    try:
        data = requests.get(f"{config.OLLAMA_URL}/api/tags", timeout=5).json()
        names = [m.get("name", "") for m in data.get("models", [])]
        return any(config.OLLAMA_MODEL.split(":")[0] in n for n in names)
    except Exception:
        return False


def pull() -> bool:
    """Stream a model pull, printing progress. Tries the modern and legacy field names."""
    for key in ("model", "name"):  # newer Ollama uses "model"; older uses "name"
        try:
            r = requests.post(f"{config.OLLAMA_URL}/api/pull",
                              json={key: config.OLLAMA_MODEL}, stream=True, timeout=None)
            if r.status_code >= 400:
                continue
            last = ""
            for line in r.iter_lines():
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                if d.get("error"):
                    print(f"  pull error: {d['error']}", flush=True)
                    break
                status = d.get("status", "")
                if d.get("total"):
                    pct = 100 * d.get("completed", 0) / d["total"]
                    print(f"  {status}: {pct:.0f}%   ", end="\r", flush=True)
                elif status and status != last:
                    print(f"  {status}", flush=True)
                    last = status
            print("\n  done.", flush=True)
            return has_model()
        except Exception as e:
            print(f"  pull attempt with '{key}' failed: {e}", flush=True)
    return False


def main():
    print(f"[ensure_model] Target model: {config.OLLAMA_MODEL} at {config.OLLAMA_URL}", flush=True)
    if not wait_for_server():
        print("[ensure_model] Ollama not reachable in time — the API will still start, "
              "but answers will be unavailable until Ollama is up.", flush=True)
        sys.exit(0)  # don't block app startup
    if has_model():
        print("[ensure_model] Model already present.", flush=True)
        return
    print("[ensure_model] Pulling model (first run only — can take a few minutes)...", flush=True)
    if not pull():
        print("[ensure_model] Could not confirm the model pulled. The API will start anyway.",
              flush=True)


if __name__ == "__main__":
    main()
