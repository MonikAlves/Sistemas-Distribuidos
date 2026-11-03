import zmq
from constPS import * #-
import platform
import random
import socket
import time



NOTICIAS = [
    "ZeroMQ desacopla produtores e consumidores",
    "Pub-sub não garante entrega para quem conecta tarde",
    "Pipeline distribui tarefas entre workers",
    "AWS: instâncias EC2 conversando via ZeroMQ",
]


def gerar_mensagens(seq):
    # O primeiro "token" de cada mensagem é o tópico, que o SUB usa para filtrar
    mensagens = [
        f"TIME {seq} {time.asctime()}",
        f"TEMP {seq} {random.uniform(15, 35):.1f}",
    ]
    # Notícias saem com menos frequência (a cada 3 ciclos)
    if seq % 3 == 0:
        mensagens.append(f"NEWS {seq} {random.choice(NOTICIAS)}")
    return mensagens


def main():
    context = zmq.Context()
    # Socket publicador (PUB), escutando em todas as interfaces
    s = context.socket(zmq.PUB)
    s.bind(f"tcp://*:{PORT}")

    maquina = f"{socket.gethostname()} ({platform.system()})"
    print("=" * 60)
    print(f"Publisher em {maquina} na porta {PORT}...")
    print(f"Tópicos: TIME, TEMP e NEWS, a cada {INTERVALO:g} s (Ctrl+C para parar)")
    print("=" * 60, flush=True)

    seq = 0
    try:
        while True:
            time.sleep(INTERVALO)
            seq += 1  # número de sequência, para o subscriber detectar mensagens perdidas
            for msg in gerar_mensagens(seq):
                s.send_string(msg)
                print(f" <- Publicado: {msg}", flush=True)

    except KeyboardInterrupt:
        print("\nPublisher finalizado pelo usuário.")
    finally:
        s.close(linger=0)
        context.term()


if __name__ == "__main__":
    main()
