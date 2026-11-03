import os
from pathlib import Path

# Lê o arquivo .env se ele existir na pasta
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                chave, valor = line.split("=", 1)
                os.environ.setdefault(chave.strip(), valor.strip())

# Se não estiver no .env, roda tudo em 127.0.0.1 com 20 tarefas por fonte
SRC1 = os.getenv("PIPE_SRC1", "127.0.0.1")   # máquina da fonte de tarefas 1
SRC2 = os.getenv("PIPE_SRC2", "127.0.0.1")   # máquina da fonte de tarefas 2
SINK = os.getenv("PIPE_SINK", "127.0.0.1")   # máquina do coletor de resultados
PORT1 = int(os.getenv("PIPE_PORT1", "4567"))
PORT2 = int(os.getenv("PIPE_PORT2", "4568"))
PORT3 = int(os.getenv("PIPE_PORT3", "4569"))  # porta do sink
TAREFAS = int(os.getenv("PIPE_TAREFAS", "20"))  # tarefas geradas por fonte
