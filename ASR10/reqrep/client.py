import zmq
from constCS import * #-
import argparse
import time



def conectar(context):
    # Socket de requisição (REQ)
    s = context.socket(zmq.REQ)
    # Não trava para sempre se o servidor cair
    s.setsockopt(zmq.RCVTIMEO, 5000)
    # Conectado às duas portas do servidor: o REQ alterna as requisições entre elas (round-robin)
    s.connect(f"tcp://{HOST}:{PORT1}")
    s.connect(f"tcp://{HOST}:{PORT2}")
    return s


def enviar_requisicao(s, op, args):
    # Envia a requisição e devolve (resposta, tempo em ms)
    inicio = time.perf_counter()
    s.send_json({"op": op, "args": args})
    try:
        resposta = s.recv_json()
    except zmq.Again:
        return None, 0
    return resposta, (time.perf_counter() - inicio) * 1000


def exibir_resposta(op, args, resposta, ms):
    if not resposta:
        print(f"   Sem resposta do servidor em {HOST}:{PORT1}/{PORT2} (timeout de 5 s).")
        print("   Verifique se o server.py está rodando.")
        return

    if resposta.get("status") == "ok":
        print(f"    {op}{tuple(args)} = {resposta.get('result')}  [{resposta.get('server')}, {ms:.2f} ms]")
    else:
        print(f"    {op}{tuple(args)} = ERRO: {resposta.get('error')}  [{resposta.get('server')}, {ms:.2f} ms]")


def rodar_demo(s):
    print("\n" + "=" * 60)
    print("DEMO - TESTES DAS NOVAS FUNCIONALIDADES (REQ-REP)")
    print("=" * 60)

    testes = [
        ("1) Operações disponíveis no servidor", "operacoes", []),
        ("2) Manipulação de texto", "maiuscula", ["hello", "world"]),
        ("", "inverter", ["sistemas distribuidos"]),
        ("", "contar_palavras", ["zeromq req rep pub sub pipeline"]),
        ("3) Operação matemática", "soma", [10, 20, 12.5]),
        ("4) Utilitário", "hora", []),
        ("5) Tratamento de erros (valor inválido e operação inexistente)", "soma", [10, "abc"]),
        ("", "xyz", []),
        ("6) Estatísticas de requisições atendidas", "estatisticas", []),
    ]

    for titulo, op, args in testes:
        if titulo:
            print(f"\n{titulo}")
        resposta, ms = enviar_requisicao(s, op, args)
        exibir_resposta(op, args, resposta, ms)
        if not resposta:
            break  # depois de um timeout o socket REQ não pode mais ser usado

    print("\n" + "=" * 60)
    print("Fim da demonstração.")
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Cliente ZeroMQ REQ (ASR10)")
    parser.add_argument("--op", help="envia uma operação avulsa (ex.: --op maiuscula --args ola mundo)")
    parser.add_argument("--args", nargs="*", default=[], help="argumentos da operação avulsa")
    parser.add_argument("--stop", action="store_true", help="pede para o servidor encerrar")
    opcoes = parser.parse_args()

    context = zmq.Context()
    s = conectar(context)
    print(f"Servidor: {HOST}:{PORT1} e {HOST}:{PORT2}")

    try:
        if opcoes.stop:
            resposta, ms = enviar_requisicao(s, "STOP", [])
            exibir_resposta("STOP", [], resposta, ms)
        elif opcoes.op:
            resposta, ms = enviar_requisicao(s, opcoes.op, opcoes.args)
            exibir_resposta(opcoes.op, opcoes.args, resposta, ms)
        else:
            rodar_demo(s)
    finally:
        s.close(linger=0)
        context.term()


if __name__ == "__main__":
    main()
