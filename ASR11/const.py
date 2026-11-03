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

# Endereço do serviço de nomes: o único que servidores e clientes precisam conhecer.
# Se não estiver no .env, usa 127.0.0.1 e porta 50051 por padrão
NS_HOST = os.getenv("NS_HOST", "127.0.0.1")
NS_PORT = int(os.getenv("NS_PORT", "50051"))

# IP que os servidores anunciam no serviço de nomes (vazio = descobre sozinho)
APP_HOST = os.getenv("APP_HOST", "")

# Nomes lógicos dos serviços de aplicação
CALC_NAME = "Calculator"
TEXT_NAME = "TextService"
