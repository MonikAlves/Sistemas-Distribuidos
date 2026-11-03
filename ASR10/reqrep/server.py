import zmq
from constCS import * #-
import datetime
import platform
import socket



OPERACOES = ["maiuscula", "inverter", "contar_palavras", "soma", "hora", "operacoes", "estatisticas"]


def executar_operacao(op, args, atendidas):
    op = (op or "").strip().lower()

    try:
        # Operações com strings
        if op in ("maiuscula", "upper"):
            if not args:
                return {"status": "error", "error": "Informe uma palavra ou frase"}
            return {"status": "ok", "result": " ".join(map(str, args)).upper()}

        elif op in ("inverter", "reverse"):
            if not args:
                return {"status": "error", "error": "Informe uma palavra ou frase"}
            return {"status": "ok", "result": " ".join(map(str, args))[::-1]}

        elif op in ("contar_palavras", "word_count"):
            if not args:
                return {"status": "error", "error": "Informe um texto para contagem"}
            total = len(" ".join(map(str, args)).split())
            return {"status": "ok", "result": total}

        # Operação matemática
        elif op in ("soma", "add"):
            if len(args) < 2:
                return {"status": "error", "error": "A soma precisa de pelo menos 2 valores"}
            res = sum(float(x) for x in args)
            return {"status": "ok", "result": int(res) if res.is_integer() else res}

        # Utilitários
        elif op in ("hora", "time"):
            agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            return {"status": "ok", "result": agora}

        elif op in ("operacoes", "ops"):
            return {"status": "ok", "result": OPERACOES}

        elif op in ("estatisticas", "stats"):
            # Quantas requisições de cada operação o servidor já atendeu
            return {"status": "ok", "result": dict(atendidas)}

        else:
            return {
                "status": "error",
                "error": f"Operação '{op}' não reconhecida. Opções: {', '.join(OPERACOES)}"
            }

    except ValueError:
        return {"status": "error", "error": "Erro de conversão: informe números válidos"}
    except Exception as e:
        return {"status": "error", "error": f"Erro inesperado: {str(e)}"}


def main():
    context = zmq.Context()
    # Socket de resposta (REP), escutando em todas as interfaces nas duas portas
    s = context.socket(zmq.REP)
    s.bind(f"tcp://*:{PORT1}")
    s.bind(f"tcp://*:{PORT2}")
    # Timeout no recv para o Ctrl+C funcionar também no Windows
    s.setsockopt(zmq.RCVTIMEO, 1000)

    # Identifica a máquina que respondeu (hostname + sistema operacional)
    maquina = f"{socket.gethostname()} ({platform.system()})"
    atendidas = {}

    print("=" * 60)
    print(f"Servidor REP em {maquina} nas portas {PORT1} e {PORT2}...")
    print("Aguardando requisições (Ctrl+C ou operação STOP para parar)...")
    print("=" * 60, flush=True)

    try:
        while True:
            try:
                req = s.recv_json()
            except zmq.Again:
                continue

            op = req.get("op", "")
            args = req.get("args", [])
            if not isinstance(args, list):
                args = [args]
            print(f" -> Requisição recebida: {req}", flush=True)

            # No original o servidor saía sem responder e o cliente ficava preso esperando
            if op == "STOP":
                s.send_json({"status": "ok", "result": "Servidor encerrado", "server": maquina})
                print("\nServidor finalizado pela operação STOP.")
                break

            resposta = executar_operacao(op, args, atendidas)
            atendidas[op] = atendidas.get(op, 0) + 1
            resposta["server"] = maquina
            s.send_json(resposta)

    except KeyboardInterrupt:
        print("\nServidor finalizado pelo usuário.")
    finally:
        s.close(linger=0)
        context.term()


if __name__ == "__main__":
    main()
