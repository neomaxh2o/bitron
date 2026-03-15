#!/usr/bin/env python3
# memory/scripts/test_memory.py
import memory_api

# 1. Crear un deploy de prueba
run_id = memory_api.start_deploy("test_deploy", details="Demo deployment")
print("Run ID", run_id)

# 2. Registrar 3 pasos
step1 = memory_api.add_step(run_id, "step1", "initialisation")
step2 = memory_api.add_step(run_id, "step2", "configuration")
step3 = memory_api.add_step(run_id, "step3", "finalisation")
print("Step IDs", step1, step2, step3)

# 3. Marcar 2 success
memory_api.finish_step(step1, status="success", output="ok")
memory_api.finish_step(step2, status="success", output="ok")

# 4. Marcar 1 failed
memory_api.finish_step(step3, status="failed", output="error msg")
# 5. Registrar error
memory_api.register_error(run_id, step3, "segmentation fault in step3")

# 6. Guardar artifact
memory_api.add_artifact(run_id, "/tmp/test_artifact.txt", "log")

# Memoria semántica
entry1 = memory_api.add_semantic_memory("deploy nginx", "Deploy nginx")
entry2 = memory_api.add_semantic_memory("rollback docker compose", "Rollback docker compose")
entry3 = memory_api.add_semantic_memory("incidente ollama path", "Incident ollama path")

# Relaciones semánticas
memory_api.link_memories(entry1, entry2, "related")
memory_api.link_memories(entry2, entry3, "caused by")

# Fin del deploy
memory_api.finish_deploy(run_id, status="completed", details="All tests passed with logs")

print("Test completed.")
