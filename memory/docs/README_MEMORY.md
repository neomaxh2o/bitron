# Memoria de Bitron

## 1. Propósito de la memoria técnica
Esta sección se mantiene igual y no necesita actualización.

## 2. Propósito de la memoria semántica
La Memoria Semántica (V1) guardaba temas, categorías, resúmenes y fuentes de cada registro de conocimiento.  Con la V2 la tabla **semantic_memory** se extiende para incluir embeddings que permiten la búsqueda semántica y el aprendizaje automático.

## 3. Ubicación de la base de datos
Se encuentra dentro del workspace de Bitron:
```
/home/neomax/.openclaw/workspace-bitron/memory/db/bitron_memory.db
```
La carpeta `memory/db/` contiene el archivo SQLite y soporta backups.

## 4. Tablas principales
| Tabla | Descripción |
|-------|-------------|
| `deploy_runs` | Registra los despliegues globales. |
| `deploy_steps` | Pasos individuales. |
| `deploy_errors` | Errores relacionados. |
| `system_artifacts` | Artifacts generados. |
| `semantic_memory` | V1 + columnas de embedding. |
| `semantic_embeddings` (opcional) | Almacena embeddings como BLOB (usado por la V2). |

## 5. **SEMANTIC MEMORY V2**
### 5.1 Nuevas columnas en `semantic_memory`
| Columna | Tipo | Descripción |
|---------|------|-------------|
| `embedding_model` | `TEXT` | Nombre del modelo usado para generar el vector. |
| `embedding_vector` | `TEXT` | Vector serializado (JSON) de las `EMBEDDING_DIM` dimensiones. |
| `embedding_dimensions` | `INTEGER` | Dimensión del vector (p.e. 256). |
| `embedding_created_at` | `TEXT` | Hora UTC de creación del vector. |

### 5.2 Embedding Vector
- Se almacena como cadena JSON para que SQLite la mantenga sin modificación.  Se puede serializar/descodificar en Python con `json.dumps()`/`json.loads()`.  <br>
- Algunos desarrolladores prefieren BLOB para un rendimiento máximo; cambiar el tipo de columna a `BLOB` y usar `sqlite3.Binary()` en la API.

### 5.3 Fallback local vs Embedding real
|  | Fallback local (MODE A) | Embedding real (MODE B) |
|---|-----------------------|-------------------------|
| Algoritmo | SHA‑256 + escala → 256‑dim sort‑vector. Determinista y sin dependencias externas. | Usa cualquier modelo que devuelva vectores (e.g., “all-MiniLM-L6-v2”, “bge‑small”). Aumenta precisión. |
| Dependencias | Ninguna | `sentence-transformers`, `torch`, etc. (debe instalarse manualmente). |
| Rendimiento | Muy bajo | Depende del modelo; puede requerir GPU. |
| Evita costo | ✔ | ❌ |

### 5.4 Regenerar Embeddings
1. **Recargar una sola memoria**``"⟨refresh_semantic_embedding(entry_id)"``
2. **Recargar todas faltantes**``"⟨refresh_all_semantic_embeddings()"``
3. En la API de `memory_api.py`: `refresh_semantic_embedding()` y `refresh_all_semantic_embeddings()` ya están implementadas.

### 5.5 Búsqueda semántica
1. Llamar a `semantic_search(query, top_k=5)`.
2. Internamente: 
   * Genera embedding del query (fallback o real). 
   * Calcula similitud coseno con cada vector almacenado. 
   * Ordena y devuelve: `id`, `topic`, `category`, `summary`, `score`.

### 5.6 Migrar a un modelo real
1. Instalar el modelo deseado (ej. `pip install sentence-transformers`).
2. Modificar la clase `_RealProvider` en `embedding_provider.py`: 
   ```python
   class _RealProvider:
       def __init__(self, model_name='sentence-transformers/all-MiniLM-L6-v2'):
           from sentence_transformers import SentenceTransformer
           self.model = SentenceTransformer(model_name)
       def embed_text(self, text):
           return self.model.encode([text], convert_to_numpy=True)[0].tolist()
   ```
3. Cambiar `MODE = 1` o llamar en la API con `mode=1`.
4. Regenerar embeddings con `refresh_all_semantic_embeddings()` para usar el nuevo modelo.
5. La tabla y las columnas de V2 permanecen igual, solo el vector cambia.

## 6. Puntos importantes
- Los datos V1 son CELEBROS: las columnas ya creadas siguen presentes y se siguen usando.
- La tabla `semantic_memory` ahora incluye la columna `embedding_vector`, pero no es obligatoria para V1.
- Las funciones de búsqueda y actualización de embeddings ya están en `memory_api.py` (juntamente con `semantic_embeddings.py`).
- Los backups de la BD se realizan con el script de migración en `memory/scripts/init_memory.py` y el `backup_memory.sh`.

---

Con esta actualización, Bitron tiene una capa de búsqueda semántica robusta, extensible y sin dependencias externas, lista para crecer cuando el modelo real esté disponible.
