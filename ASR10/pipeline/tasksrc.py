import zmq
from constPipe import * #-
import argparse
import pickle
import random
import time



def main():
    parser = argparse.ArgumentParser(description="Fonte de tarefas ZeroMQ PUSH (ASR10)")
    parser.add_argument("id", choices=["1", "2"], help="número da fonte (define a porta usada)")
    opcoes = parser.parse_args()
    eu = opcoes.id
    porta = PORT1 if eu == "1" else PORT2

    context = zmq.Context()
    # Socket PUSH, escutando em todas as interfaces
    s = context.socket(zmq.PUSH)
    s.bind(f"tcp://*:{porta}")

    print("=" * 60)
    print(f"Fonte {eu} na porta {porta}, aguardando os workers conectarem...")
    print("=" * 60, flush=True)
    # Dá tempo dos workers conectarem antes de começar a enviar
    time.sleep(3)

    try:
        for i in range(TAREFAS):
            time.sleep(0.2)
            carga = random.randint(1, 100)
            # Leva a hora de criação para o sink medir o tempo total da tarefa
            s.send(pickle.dumps((eu, i, carga, time.time())))
            print(f" <- Tarefa {i} enviada (carga {carga})", flush=True)

        print(f"\nFonte {eu} terminou de enviar {TAREFAS} tarefas.")
        time.sleep(1)  # deixa as últimas mensagens saírem

    except KeyboardInterrupt:
        print("\nFonte finalizada pelo usuário.")
    finally:
        s.close()
        context.term()


if __name__ == "__main__":
    main()
