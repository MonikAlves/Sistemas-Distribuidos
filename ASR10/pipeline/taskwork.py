import zmq
from constPipe import * #-
import argparse
import pickle
import platform
import socket
import time



def contar_primos(limite):
    # Crivo de Eratóstenes: trabalho de verdade no lugar do sleep do exemplo original
    crivo = bytearray([1]) * (limite + 1)
    crivo[0:2] = b"\x00\x00"
    for i in range(2, int(limite ** 0.5) + 1):
        if crivo[i]:
            crivo[i*i::i] = bytearray(len(crivo[i*i::i]))
    return sum(crivo)


def main():
    parser = argparse.ArgumentParser(description="Worker ZeroMQ PULL (ASR10)")
    parser.add_argument("id", help="identificação do worker")
    opcoes = parser.parse_args()
    eu = opcoes.id
    maquina = f"{socket.gethostname()}-{platform.system()}"

    context = zmq.Context()
    # Socket PULL conectado às duas fontes de tarefas
    r = context.socket(zmq.PULL)
    r.connect(f"tcp://{SRC1}:{PORT1}")
    r.connect(f"tcp://{SRC2}:{PORT2}")
    # Timeout no recv para o Ctrl+C funcionar também no Windows
    r.setsockopt(zmq.RCVTIMEO, 1000)

    # Socket PUSH que envia os resultados para o sink
    saida = context.socket(zmq.PUSH)
    saida.connect(f"tcp://{SINK}:{PORT3}")

    print("=" * 60)
    print(f"Worker {eu} iniciado em {maquina} (Ctrl+C para parar)...")
    print("=" * 60, flush=True)

    try:
        while True:
            try:
                fonte, tarefa, carga, criada_em = pickle.loads(r.recv())
            except zmq.Again:
                continue

            inicio = time.time()
            resultado = contar_primos(carga * 20000)
            tempo_trabalho = time.time() - inicio
            print(f" -> Tarefa {tarefa} da fonte {fonte} (carga {carga}): {resultado} primos", flush=True)

            saida.send(pickle.dumps({
                "worker": eu,
                "maquina": maquina,
                "fonte": fonte,
                "tarefa": tarefa,
                "carga": carga,
                "resultado": resultado,
                "tempo_trabalho": tempo_trabalho,
                "tempo_total": time.time() - criada_em,
            }))

    except KeyboardInterrupt:
        print("\nWorker finalizado pelo usuário.")
    finally:
        r.close(linger=0)
        saida.close(linger=0)
        context.term()


if __name__ == "__main__":
    main()
