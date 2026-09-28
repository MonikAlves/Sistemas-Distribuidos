from socket  import *
from constCS import * #-
import json
import sys



def enviar_requisicao(payload):
    s = socket(AF_INET, SOCK_STREAM)
    try:
        s.connect((HOST, PORT))
    except ConnectionRefusedError:
        print(f"\n Não foi possível conectar ao servidor em {HOST}:{PORT}.")
        print(" Verifique se o server.py está rodando em outro terminal.")
        return None

    try:
        # Envia a mensagem com delimitador de nova linha
        msg = json.dumps(payload, ensure_ascii=False) + "\n"
        s.sendall(msg.encode("utf-8"))

        # Aguarda a resposta do servidor
        buffer = ""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            buffer += chunk.decode("utf-8")
            if "\n" in buffer:
                break

        linha = buffer.strip()
        if not linha:
            return None
        return json.loads(linha)
    finally:
        s.close()


def exibir_resposta(resposta):
    if not resposta:
        print("   Nenhuma resposta recebida do servidor.")
        return

    if resposta.get("status") != "success":
        print(f"   Erro no servidor: {resposta.get('error')}")
        return

    resultados = resposta.get("results", [])
    print(f"  Total de operações processadas: {len(resultados)}")
    for i, item in enumerate(resultados, start=1):
        op = item.get("op")
        args = item.get("args")
        if item.get("status") == "ok":
            print(f"    {i}. {op}{tuple(args)} = {item.get('result')}")
        else:
            print(f"    {i}. {op}{tuple(args)} = ERRO: {item.get('error')}")


def rodar_demo():
    print("\n" + "=" * 60)
    print("DEMO - TESTES DOS REQUISITOS DO TRABALHO")
    print("=" * 60)

    # 1. Operação matemática simples
    print("\n1) Requisição única: Soma de valores")
    req1 = {"op": "soma", "args": [10, 25, 15]}
    resp1 = enviar_requisicao(req1)
    exibir_resposta(resp1)

    # 2. Operação com string
    print("\n2) Requisição única: Manipulação de texto (inverter frase)")
    req2 = {"op": "inverter", "args": ["Sistemas Distribuidos"]}
    resp2 = enviar_requisicao(req2)
    exibir_resposta(resp2)

    # 3. REQUISITO PRINCIPAL: Chamar mais de uma funcionalidade na mesma requisição
    print("\n3) Múltiplas funcionalidades na mesma requisição (Batch):")
    print("   Enviando juntos: potência, raiz, multiplicação, maiúscula e contagem de palavras")
    req3 = {
        "operations": [
            {"op": "potencia", "args": [2, 8]},
            {"op": "raiz", "args": [144]},
            {"op": "multiplicacao", "args": [6, 7]},
            {"op": "maiuscula", "args": ["teste de lote"]},
            {"op": "contar_palavras", "args": ["exercicio de sistemas distribuidos"]}
        ]
    }
    resp3 = enviar_requisicao(req3)
    exibir_resposta(resp3)

    # 4. Tratamento de erros (divisão por zero e raiz negativa)
    print("\n4) Testando tratamento de erros (divisão por zero e raiz negativa)")
    req4 = {
        "operations": [
            {"op": "divisao", "args": [50, 2]},
            {"op": "divisao", "args": [50, 0]},
            {"op": "raiz", "args": [-25]}
        ]
    }
    resp4 = enviar_requisicao(req4)
    exibir_resposta(resp4)

    print("\n" + "=" * 60)
    print("Fim da demonstração.")
    print("=" * 60 + "\n")


def menu():
    while True:
        print("\n--- CLIENTE TCP (Capítulo 2) ---")
        print(f"Servidor: {HOST}:{PORT}")
        print("1. Enviar uma operação")
        print("2. Enviar várias operações juntas (mesma requisição)")
        print("3. Rodar demonstração automática (--demo)")
        print("0. Sair")
        opcao = input("Opção: ").strip()

        if opcao == "1":
            print("\nOperações: soma, subtracao, multiplicacao, divisao, potencia, raiz, porcentagem, maiuscula, minuscula, inverter, contar_palavras, hora, eco")
            op = input("Nome da operação: ").strip()
            args_raw = input("Argumentos (separados por espaço): ").strip()
            args = args_raw.split() if args_raw else []

            req = {"op": op, "args": args}
            resp = enviar_requisicao(req)
            exibir_resposta(resp)

        elif opcao == "2":
            print("\nAdicione as operações que deseja incluir nesta requisição:")
            lista = []
            while True:
                op = input(f"Operação #{len(lista)+1} (ou 'enviar' para mandar, 'cancelar' para sair): ").strip()
                if op.lower() == "enviar":
                    if not lista:
                        print("Nenhuma operação foi adicionada.")
                        break
                    req = {"operations": lista}
                    resp = enviar_requisicao(req)
                    exibir_resposta(resp)
                    break
                elif op.lower() == "cancelar":
                    print("Cancelado.")
                    break
                elif not op:
                    continue

                args_raw = input(f"  Argumentos para '{op}': ").strip()
                args = args_raw.split() if args_raw else []
                lista.append({"op": op, "args": args})

        elif opcao == "3":
            rodar_demo()

        elif opcao == "0":
            print("Encerrando cliente...")
            break
        else:
            print("Opção inválida, tente de novo.")


if __name__ == "__main__":
    if "--demo" in sys.argv:
        rodar_demo()
    elif "--op" in sys.argv:
        idx = sys.argv.index("--op") + 1
        op_name = sys.argv[idx]
        args = []
        if "--args" in sys.argv:
            args = sys.argv[sys.argv.index("--args") + 1:]
        resp = enviar_requisicao({"op": op_name, "args": args})
        exibir_resposta(resp)
    else:
        menu()
