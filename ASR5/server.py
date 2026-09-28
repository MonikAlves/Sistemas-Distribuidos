from socket  import *
from constCS import * #-
import argparse
import json
import math
import datetime
import threading
import time



def executar_operacao(op, args):
    op = (op or "").strip().lower()

    try:
        # Operações matemáticas básicas
        if op in ("soma", "add"):
            if len(args) < 2:
                return {"status": "error", "error": "A soma precisa de pelo menos 2 valores"}
            valores = [float(x) for x in args]
            res = sum(valores)
            return {"status": "ok", "result": int(res) if res.is_integer() else res}

        elif op in ("subtracao", "sub"):
            if len(args) != 2:
                return {"status": "error", "error": "A subtração precisa de 2 valores"}
            res = float(args[0]) - float(args[1])
            return {"status": "ok", "result": int(res) if res.is_integer() else res}

        elif op in ("multiplicacao", "mul"):
            if len(args) < 2:
                return {"status": "error", "error": "A multiplicação precisa de pelo menos 2 valores"}
            valores = [float(x) for x in args]
            res = math.prod(valores)
            return {"status": "ok", "result": int(res) if res.is_integer() else res}

        elif op in ("divisao", "div"):
            if len(args) != 2:
                return {"status": "error", "error": "A divisão precisa de 2 valores (dividendo e divisor)"}
            divisor = float(args[1])
            # Evita que o servidor caia com erro de divisão por zero
            if divisor == 0:
                return {"status": "error", "error": "Divisão por zero não é permitida"}
            res = float(args[0]) / divisor
            return {"status": "ok", "result": int(res) if res.is_integer() else round(res, 4)}

        elif op in ("potencia", "pow"):
            if len(args) != 2:
                return {"status": "error", "error": "A potência precisa de base e expoente"}
            res = math.pow(float(args[0]), float(args[1]))
            return {"status": "ok", "result": int(res) if res.is_integer() else res}

        elif op in ("raiz", "sqrt"):
            if len(args) != 1:
                return {"status": "error", "error": "A raiz quadrada precisa de 1 valor"}
            val = float(args[0])
            if val < 0:
                return {"status": "error", "error": "Não existe raiz real de número negativo"}
            res = math.sqrt(val)
            return {"status": "ok", "result": int(res) if res.is_integer() else round(res, 4)}

        elif op in ("porcentagem", "pct"):
            if len(args) != 2:
                return {"status": "error", "error": "Porcentagem precisa de valor e taxa percentual"}
            res = (float(args[0]) * float(args[1])) / 100.0
            return {"status": "ok", "result": int(res) if res.is_integer() else res}

        # Operações com strings
        elif op in ("maiuscula", "upper"):
            if not args:
                return {"status": "error", "error": "Informe uma palavra ou frase"}
            return {"status": "ok", "result": str(args[0]).upper()}

        elif op in ("minuscula", "lower"):
            if not args:
                return {"status": "error", "error": "Informe uma palavra ou frase"}
            return {"status": "ok", "result": str(args[0]).lower()}

        elif op in ("inverter", "reverse"):
            if not args:
                return {"status": "error", "error": "Informe uma palavra ou frase"}
            return {"status": "ok", "result": str(args[0])[::-1]}

        elif op in ("contar_palavras", "word_count"):
            if not args:
                return {"status": "error", "error": "Informe um texto para contagem"}
            total = len(str(args[0]).split())
            return {"status": "ok", "result": total}

        # Utilitários simples
        elif op in ("hora", "time"):
            agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            return {"status": "ok", "result": agora}

        elif op in ("eco", "echo"):
            msg = str(args[0]) if args else ""
            return {"status": "ok", "result": f"{msg}*"}

        else:
            return {
                "status": "error",
                "error": f"Operação '{op}' não reconhecida. Opções: soma, subtracao, multiplicacao, divisao, potencia, raiz, porcentagem, maiuscula, minuscula, inverter, contar_palavras, hora, eco"
            }

    except ValueError:
        return {"status": "error", "error": "Erro de conversão: informe números válidos"}
    except Exception as e:
        return {"status": "error", "error": f"Erro inesperado: {str(e)}"}


def processar_requisicao(mensagem_bruta):
    try:
        dados = json.loads(mensagem_bruta)
    except Exception:
        return {"status": "error", "error": "Mensagem inválida, esperado formato JSON"}

    # Caso 1: o cliente enviou uma lista de operações na mesma requisição
    if "operations" in dados and isinstance(dados["operations"], list):
        lista_ops = dados["operations"]
    # Caso 2: o cliente enviou uma operação avulsa
    elif "op" in dados:
        lista_ops = [dados]
    else:
        return {"status": "error", "error": "Formato de requisição sem 'op' ou 'operations'"}

    resultados = []
    for item in lista_ops:
        nome_op = item.get("op", "")
        args = item.get("args", [])
        if not isinstance(args, list):
            args = [args]

        saida = executar_operacao(nome_op, args)
        info = {
            "op": nome_op,
            "args": args,
            "status": saida.get("status")
        }
        if saida.get("status") == "ok":
            info["result"] = saida.get("result")
        else:
            info["error"] = saida.get("error")
        resultados.append(info)

    return {
        "status": "success",
        "total": len(resultados),
        "results": resultados
    }


def atender_conexao(conn, addr, atraso, verbose):
    # Mesmo laço de atendimento da ASR4, agora isolado numa função para poder
    # ser executado tanto na thread principal (modo single) quanto numa thread nova (modo multi)
    if verbose:
        print(f"\n[+] Cliente conectado: {addr[0]}:{addr[1]} ({threading.current_thread().name})")

    try:
        buffer = ""
        while True:
            dados = conn.recv(4096)
            if not dados:
                break  # Cliente desconectou

            buffer += dados.decode("utf-8")
            # Mensagens separadas por quebra de linha (\n)
            while "\n" in buffer:
                linha, buffer = buffer.split("\n", 1)
                linha = linha.strip()
                if not linha:
                    continue

                if verbose:
                    print(f" -> Requisição recebida: {linha}")
                resposta = processar_requisicao(linha)
                # Simula o custo de um processamento real (acesso a disco, banco de dados, etc.)
                if atraso > 0:
                    time.sleep(atraso)
                resposta_bytes = (json.dumps(resposta, ensure_ascii=False) + "\n").encode("utf-8")
                conn.sendall(resposta_bytes)
                if verbose:
                    print(f" <- Resposta enviada ({resposta.get('total', 0)} operações)")
    except (ConnectionResetError, ConnectionAbortedError):
        pass  # Cliente fechou a conexão de forma abrupta
    finally:
        conn.close()
        if verbose:
            print(f"[-] Conexão com {addr[0]}:{addr[1]} encerrada.")


def main():
    parser = argparse.ArgumentParser(description="Servidor TCP de operações (ASR5)")
    parser.add_argument("--modo", choices=["single", "multi"], default="multi",
                        help="single = atende uma requisição por vez (ASR4); multi = uma thread por requisição")
    parser.add_argument("--porta", type=int, default=PORT)
    parser.add_argument("--atraso", type=float, default=0.0,
                        help="tempo de processamento simulado por requisição, em milissegundos")
    parser.add_argument("--quiet", action="store_true", help="não imprime cada requisição (usado no experimento)")
    opcoes = parser.parse_args()
    atraso = opcoes.atraso / 1000.0
    verbose = not opcoes.quiet

    # Socket TCP (IPv4, streaming)
    servidor = socket(AF_INET, SOCK_STREAM)
    # Evita erro de 'Address already in use' ao reiniciar o servidor
    servidor.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

    servidor.bind(('', opcoes.porta))
    # Fila maior que na ASR4, pois agora chegam muitas conexões ao mesmo tempo
    servidor.listen(SOMAXCONN)
    # Timeout no accept para o Ctrl+C funcionar também no Windows
    servidor.settimeout(1.0)

    print("=" * 60)
    print(f"Servidor ({opcoes.modo}-threaded) rodando na porta {opcoes.porta}...")
    print(f"Atraso simulado por requisição: {opcoes.atraso} ms")
    print("Aguardando conexões dos clientes (Ctrl+C para parar)...")
    print("=" * 60, flush=True)

    try:
        while True:
            try:
                conn, addr = servidor.accept()
            except timeout:
                continue

            if opcoes.modo == "multi":
                # Uma thread nova para cada requisição recebida
                t = threading.Thread(target=atender_conexao, args=(conn, addr, atraso, verbose), daemon=True)
                t.start()
            else:
                # Atende na própria thread principal, uma requisição por vez (igual à ASR4)
                atender_conexao(conn, addr, atraso, verbose)

    except KeyboardInterrupt:
        print("\nServidor finalizado pelo usuário.")
    finally:
        servidor.close()


if __name__ == "__main__":
    main()
