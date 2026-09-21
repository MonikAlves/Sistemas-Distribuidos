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

# Se não estiver no .env, usa 127.0.0.1 e porta 5678 por padrão
HOST = os.getenv("CS_HOST", "127.0.0.1")
PORT = int(os.getenv("CS_PORT", "5678"))
