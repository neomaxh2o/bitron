#!/usr/bin/env python3
# memory/scripts/semantic_embeddings.py
import sqlite3, pathlib, json, hashlib, random
from typing import List, Optional

# ==========================
# DB path helper (same as memory_api)
DB_PATH = pathlib.Path(__file__).resolve().parents[2] / "db" / "bitron_memory.db"

# ==========================
# Fallback embeddings (hash‑based)
EMBEDDING_DIM = 256

# --- Text normalization ----------------

def normalize_text_for_embedding(text: str) -> str:
    """Simple normalization: lower‑case, strip whitespace, collapse spaces."""
    return " ".join(text.lower().split())

# --- Generate embedding --------

def generate_embedding(text: str) -> List[float]:
    """Fallback: deterministic hash → vector of floats in [0,1)."""
    norm = normalize_text_for_embedding(text)
    h = hashlib.sha256(norm.encode("utf-8")).digest()
    # Convert each 4‑byte chunk to a float in [0,1)
    vec = []
    for i in range(0, len(h), 4):
        chunk = int.from_bytes(h[i:i+4], "big", signed=False)
        vec.append(chunk / 2**32)
        if len(vec) >= EMBEDDING_DIM:
            break
    # Pad with zeros if needed
    while len(vec) < EMBEDDING_DIM:
        vec.append(0.0)
    return vec

# ==========================
# SQLite utilities

def _conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

# ==========================
# Embedding API functions

def update_memory_embedding(memory_id: int, model_name: str = "fallback") -> None:
    with _conn() as c:
        cur = c.execute("SELECT summary FROM semantic_memory WHERE entry_id=?", (memory_id,)).fetchone()
        if not cur:
            raise KeyError(f"memory_id {memory_id} not found")
        text = cur["summary"] or ""
        vec = generate_embedding(text)
        c.execute(
            "UPDATE semantic_memory SET embedding_model=?, embedding_vector=?, embedding_dimensions=?, embedding_created_at=? WHERE entry_id=?",
            (model_name, json.dumps(vec), len(vec), datetime.utcnow().isoformat() + "Z", memory_id),
        )


def update_all_missing_embeddings(model_name: str = "fallback") -> None:
    with _conn() as c:
        rows = c.execute("SELECT entry_id FROM semantic_memory WHERE embedding_vector IS NULL OR embedding_vector='' ").fetchall()
        for row in rows:
            update_memory_embedding(row["entry_id"], model_name)

# ==========================
# Cosine similarity

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    assert len(vec1) == len(vec2), "Vectors must be same dim"
    dot = sum(a*b for a,b in zip(vec1, vec2))
    norm1 = sum(a*a for a in vec1)**0.5
    norm2 = sum(b*b for b in vec2)**0.5
    return dot/(norm1*norm2) if norm1 and norm2 else 0.0

# ==========================
# Search similar memories

def search_similar_memories(query: str, top_k: int = 5) -> List[dict]:
    query_vec = generate_embedding(query)
    results = []
    with _conn() as c:
        rows = c.execute("SELECT * FROM semantic_memory WHERE embedding_vector IS NOT NULL AND embedding_vector!='' ").fetchall()
        for r in rows:
            vec = json.loads(r["embedding_vector"])
            sim = cosine_similarity(query_vec, vec)
            results.append((sim, dict(r)))
    results.sort(key=lambda x: x[0], reverse=True)
    return [r[1] for r in results[:top_k]]

if __name__ == "__main__":
    print("Testing embedding module...")
    # Example of updating a memory
    try:
        update_memory_embedding(1)
    except Exception as e:
        print("Error updating memory:", e)
    print(search_similar_memories("error deploy", top_k=3))
