#!/usr/bin/env python3
"""memory/scripts/embedding_provider.py

Este módulo ofrece una API única para obtener embeddings
y tiene la posibilidad de elegir entre dos modos:

• MODE_A – fallback determinístico basado en hashing
• MODE_B – placeholder para integrar un modelo real

No instala ni carga dependencias externas.  El código está preparado para que un evento externo
pueda inyectar el modelo real cuando el proyecto se expanda.
"""

import hashlib
import json
import random
from typing import List

# ----------------- CONFIG -----------------
# 0 → Mode A (fallback determinístico)
# 1 → Mode B (real embedding model) – no instalado aun
MODE = 0
# Dimensión del vector sin modelo real (coincide con la V2 de embeddings)
EMBEDDING_DIM = 256

# ----------------- FALLBACK (Mode A) -----------------

def _normalize(text: str) -> str:
    """Simple normalización: lower‑case y quitar espacios extra."""
    return " ".join(text.lower().split())


def _fallback_embedding(text: str) -> List[float]:
    """Deterministic 256‑dim vector generado con SHA256 + scale.
    Se garantiza que la misma entrada devuelve el mismo vector.
    """
    norm = _normalize(text)
    h = hashlib.sha256(norm.encode("utf-8")).digest()
    vec: List[float] = []
    for i in range(0, len(h), 4):
        chunk = int.from_bytes(h[i:i+4], "big", signed=False)
        vec.append(chunk / 2**32)
        if len(vec) >= EMBEDDING_DIM:
            break
    while len(vec) < EMBEDDING_DIM:
        vec.append(0.0)
    return vec

# ----------------- PLACEHOLDER (Mode B) -----------------
class _RealProvider:
    """Placeholder que debe cargar un modelo real.
    """
    def __init__(self, model_name: str = "fallback"):
        self.model_name = model_name
        # El modelo real debe ser cargado aquí, p.e.:
        # from sentence_transformers import SentenceTransformer
        # self.model = SentenceTransformer(model_name)
        raise NotImplementedError("Real embedding model not yet integrated.")

    def embed_text(self, text: str) -> List[float]:
        # Con el modelo real:
        # return self.model.encode([text], convert_to_numpy=True)[0].tolist()
        raise NotImplementedError

# ----------------- API -----------------

def get_embedding_provider(mode: int = 0):
    """Devuelve la instancia adecuada:
    • 0 → fallback
    • 1 → real provider (solo si se implementa!)
    """
    if mode == 0:
        return _fallback_embedding
    elif mode == 1:
        return _RealProvider()  # Pasará de error hasta que se instale la librería
    else:
        raise ValueError("Unsupported embed mode: {}".format(mode))


def embed_text(text: str, mode: int = 0) -> List[float]:
    """Única API para obtener embeddings.
    Se delega en el proveedor correcto.
    """
    provider = get_embedding_provider(mode)
    if callable(provider):
        # fallback func
        return provider(text)
    # Si no es callable, se asume instancia de provider
    return provider.embed_text(text)

# ===================== TEST =======
if __name__ == "__main__":
    txt = "deploy nginx"
    print("fallback:", embed_text(txt, mode=0)[:5], "...")
    try:
        print("real:", embed_text(txt, mode=1)[:5])
    except Exception as e:
        print("real mode not ready:", e)
