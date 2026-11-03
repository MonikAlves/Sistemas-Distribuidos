import zmq
from constPipe import * #-
import pickle



def exibir_resumo(por_worker, tempo_total, total):
    print("\n" + "=" * 60)
    print("RESUMO")
    print("=" * 60)
    for chave, w in sorted(por_worker.items()):
        print(f"{chave:20} tarefas: {w['tarefas']:3}  carga total: {w['carga']:5}  fontes: {sorted(w['fontes'])}")
    print(f"Tempo médio fonte -> resultado: {tempo_total / total:.3f} s")
    print("=" * 60)


def main():
    total = 2 * TAREFAS  # duas fontes, TAREFAS tarefas cada

    context = zmq.Context()
    # Socket PULL que recebe os resultados de todos os workers
    r = context.socket(zmq.PULL)
    r.bind(f"tcp://*:{PORT3}")
    # Timeout no recv para o Ctrl+C funcionar também no Windows
    r.setsockopt(zmq.RCVTIMEO, 1000)

    print("=" * 60)
    print(f"Sink na porta {PORT3}, esperando {total} resultados...")
    print("=" * 60, flush=True)

    por_worker = {}
    tempo_total = 0.0
    recebidos = 0
    try:
        while recebidos < total:
            try:
                res = pickle.loads(r.recv())
            except zmq.Again:
                continue
            recebidos += 1
            chave = f"{res['worker']}@{res['maquina']}"
            w = por_worker.setdefault(chave, {"tarefas": 0, "carga": 0, "fontes": set()})
            w["tarefas"] += 1
            w["carga"] += res["carga"]
            w["fontes"].add(res["fonte"])
            tempo_total += res["tempo_total"]
            print(f" -> Fonte {res['fonte']} tarefa {res['tarefa']:2} -> worker {chave}: "
                  f"{res['resultado']} primos ({res['tempo_trabalho']:.3f} s de trabalho)", flush=True)

        exibir_resumo(por_worker, tempo_total, total)

    except KeyboardInterrupt:
        print("\nSink finalizado pelo usuário.")
    finally:
        r.close()
        context.term()


if __name__ == "__main__":
    main()
