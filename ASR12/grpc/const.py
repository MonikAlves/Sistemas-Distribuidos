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

# Se não estiver no .env, usa 127.0.0.1 e porta 50051 por padrão
# (PORT continua string, como no exemplo original, que faz IP + ':' + PORT)
IP = os.getenv("GRPC_HOST", "127.0.0.1")
PORT = os.getenv("GRPC_PORT", "50051")
