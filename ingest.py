"""Ingest PDF(s) into ChromaDB.

Pipeline:  PDF -> extract text per page -> chunk -> embed (Chroma default MiniLM) -> store.

Run:
    python ingest.py            # build the vector DB from every PDF in ./data
    python ingest.py --reset    # wipe and rebuild
"""
import os
import re
import sys
import glob

import chromadb
from chromadb.utils import embedding_functions
from pypdf import PdfReader

import config


def extract_pages(pdf_path: str):
    """Return [(page_number, text), ...] for one PDF."""
    reader = PdfReader(pdf_path)
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = re.sub(r"[ \t]+", " ", text)          # squash runs of spaces
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        if text:
            pages.append((i, text))
    return pages


def chunk_text(text: str, size: int, overlap: int):
    """Split text into ~`size`-char chunks with `overlap` carried between them.

    Splitting happens on whitespace so we never cut a word in half.
    Overlap keeps a sentence that straddles a boundary retrievable from both chunks.
    """
    words = text.split()
    chunks, cur = [], ""
    for w in words:
        if len(cur) + len(w) + 1 <= size:
            cur = f"{cur} {w}".strip()
        else:
            chunks.append(cur)
            tail = cur[-overlap:] if overlap else ""
            cur = f"{tail} {w}".strip()
    if cur:
        chunks.append(cur)
    return chunks


def get_collection(reset: bool = False):
    client = chromadb.PersistentClient(path=config.CHROMA_PATH)
    ef = embedding_functions.DefaultEmbeddingFunction()   # all-MiniLM-L6-v2 (downloads once)
    if reset:
        try:
            client.delete_collection(config.COLLECTION_NAME)
        except Exception:
            pass
    return client.get_or_create_collection(
        name=config.COLLECTION_NAME,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},               # cosine distance for retrieval
    )


def build(reset: bool = True):
    pdfs = sorted(glob.glob(os.path.join(config.DATA_DIR, "*.pdf")))
    if not pdfs:
        print(f"No PDF found in {config.DATA_DIR}. Put the DPDP Act PDF there and re-run.")
        sys.exit(1)

    col = get_collection(reset=reset)
    docs, ids, metas = [], [], []

    for pdf in pdfs:
        name = os.path.basename(pdf)
        pages = extract_pages(pdf)
        print(f"  {name}: {len(pages)} pages with text")
        for page_no, text in pages:
            for j, chunk in enumerate(chunk_text(text, config.CHUNK_CHARS, config.CHUNK_OVERLAP)):
                docs.append(chunk)
                ids.append(f"{name}-p{page_no}-c{j}")
                metas.append({"source": name, "page": page_no})

    # Add in batches (Chroma embeds as you add)
    BATCH = 100
    for i in range(0, len(docs), BATCH):
        col.add(documents=docs[i:i + BATCH], ids=ids[i:i + BATCH], metadatas=metas[i:i + BATCH])
        print(f"  embedded {min(i + BATCH, len(docs))}/{len(docs)} chunks")

    print(f"Done. Collection '{config.COLLECTION_NAME}' now holds {col.count()} chunks "
          f"at {config.CHROMA_PATH}")


if __name__ == "__main__":
    # Always rebuild cleanly (re-adding the same ids would otherwise clash).
    build(reset=True)
