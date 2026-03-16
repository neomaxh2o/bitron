#!/usr/bin/env python3
import sqlite3, pathlib, datetime, json, hashlib, random
from typing import Optional, List

# ----- DB PATH -----
DB_DIR = pathlib.Path(__file__).resolve().parents[2] / "db"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "bitron_memory.db"

# ----- helpers -----

def _now() -> str:
    return datetime.datetime.utcnow().isoformat() + "Z"

def _conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

# ----- embedding helpers (fallback) -----
EMBEDDING_DIM = 256

def normalize_text_for_embedding(text: str) -> str:
    return " ".join(text.lower().split())

def generate_embedding(text: str) -> List[float]:
    norm = normalize_text_for_embedding(text)
    h = hashlib.sha256(norm.encode("utf-8")).digest()
    vec = []
    for i in range(0, len(h), 4):
        chunk = int.from_bytes(h[i:i+4], "big", signed=False)
        vec.append(chunk / 2**32)
        if len(vec) >= EMBEDDING_DIM:
            break
    while len(vec) < EMBEDDING_DIM:
        vec.append(0.0)
    return vec

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    dot = sum(a*b for a,b in zip(vec1, vec2))
    norm1 = sum(a*a for a in vec1)**0.5
    norm2 = sum(b*b for b in vec2)**0.5
    return dot/(norm1*norm2) if norm1 and norm2 else 0.0

# ----- API functions (existing) -----

def start_deploy(deploy_name: str, details: Optional[str] = None) -> int:
    with _conn() as conn:
        cur = conn.execute(
            "INSERT INTO deploy_runs (deploy_name, start_time, status, details) VALUES (?,?,?,?)",
            (deploy_name, _now(), 'running', details),
        )
        return cur.lastrowid

# ... other existing functions from previous memory_api ... (omitted for brevity)

# ----- New helper: refresh embedding for single memory -----

def refresh_semantic_embedding(memory_id: int, model_name: str = 'fallback') -> None:
    with _conn() as conn:
        cur = conn.execute("SELECT summary FROM semantic_memory WHERE entry_id=?", (memory_id,)).fetchone()
        if not cur:
            raise KeyError(f"memory_id {memory_id} not found")
        summary = cur["summary"] or ""
        vec = generate_embedding(summary)
        conn.execute(
            "UPDATE semantic_memory SET embedding_model=?, embedding_vector=?, embedding_dimensions=?, embedding_created_at=? WHERE entry_id=?",
            (model_name, json.dumps(vec), len(vec), _now(), memory_id),
        )

# ----- Refresh all missing embeddings -----

def refresh_all_semantic_embeddings(model_name: str = 'fallback') -> None:
    with _conn() as conn:
        rows = conn.execute("SELECT entry_id FROM semantic_memory WHERE embedding_vector IS NULL OR embedding_vector='' ").fetchall()
        for row in rows:
            refresh_semantic_embedding(row["entry_id"], model_name)

# ----- Semantic search -----

def semantic_search(query: str, top_k: int = 5) -> List[dict]:
    query_vec = generate_embedding(query)
    results = []
    with _conn() as conn:
        cur = conn.execute("SELECT * FROM semantic_memory WHERE embedding_vector IS NOT NULL AND embedding_vector!='' ")
        for row in cur:
            vec = json.loads(row["embedding_vector"])
            score = cosine_similarity(query_vec, vec)
            results.append((score, {
                "id": row["entry_id"],
                "topic": row["topic"],
                "category": row["category"],
                "summary": row["summary"],
                "score": score,
            }))
    results.sort(key=lambda x: x[0], reverse=True)
    return [r[1] for r in results[:top_k]]

# ----- modify add_semantic_memory to generate embedding automatically -----

def add_semantic_memory(topic: str, summary: str, source: Optional[str] = None, category: Optional[str] = None, generate_embed: bool = True, model_name: str = 'fallback') -> int:
    with _conn() as conn:
        cur = conn.execute(
            "INSERT INTO semantic_memory (topic, category, summary, source, created_at) VALUES (?,?,?,?,?)",
            (topic, category, summary, source, _now()),
        )
        entry_id = cur.lastrowid
        if generate_embed:
            refresh_semantic_embedding(entry_id, model_name)
        return entry_id

# ... rest of the old functions continue here ... (omitted for brevity) 

if __name__ == "__main__":
    print("Testing updated memory API...",)
    run_id = start_deploy("demo")
    print("Run ID", run_id)
    finish_deploy(run_id)
    print("Done")
