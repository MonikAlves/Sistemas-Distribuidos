from socket  import *
from constCS import * #-
import argparse
import json
import random
import statistics
import struct
import threading
import time



PALAVRAS = ["sistemas", "distribuidos", "ufg", "socket", "thread", "cliente",
            "servidor", "rede", "processo", "mensagem", "tcp", "concorrencia"]


def gerar_operacao(rng):
    # Sorteia uma operação e gera argumentos aleatórios compatíveis com ela
    op = rng.choice(["soma", "subtracao", "multiplicacao", "divisao", "potencia", "raiz",
                     "porcentagem", "maiuscula", "minuscula", "inverter", "contar_palavras", "eco"])

    if op in ("soma", "multiplicacao"):
        args = [rng.randint(-100, 100) for _ in range(rng.randint(2, 5))]
    elif op in ("subtracao", "divisao"):
        # O divisor pode ser 0 de vez em quando, para exercitar o tratamento de erro
        args = [rng.randint(-1000, 1000), rng.randint(0, 50)]
    elif op == "potencia":
        args = [rng.randint(1, 10), rng.randint(0, 8)]
    elif op == "raiz":
        args = [rng.randint(-10, 10000)]
    elif op == "porcentagem":
        args = [rng.randint(0, 10000), rng.randint(1, 100)]
    else:
        args = [" ".join(rng.choices(PALAVRAS, k=rng.randint(1, 6)))]

    return {"op": op, "args": args}


def gerar_requisicao(rng):
    # 70% das requisições têm uma operação avulsa e 30% são lotes de 2 a 5 operações
    if rng.random() < 0.7:
        return gerar_operacao(rng)
    return {"operations": [gerar_operacao(rng) for _ in range(rng.randint(2, 5))]}


def enviar_requisicao(payload, host=HOST, port=PORT):
    s = socket(AF_INET, SOCK_STREAM)
    # Ao fechar, descarta a conexão na hora (RST) em vez de deixá-la em TIME_WAIT.
    # Sem isso, milhares de requisições seguidas esgotam as portas efêmeras do sistema operacional.
    s.setsockopt(SOL_SOCKET, SO_LINGER, struct.pack("ii", 1, 0))
    try:
        s.connect((host, port))

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


def enviar_e_medir(payload, servidor):
    # Envia uma requisição e devolve (latência em segundos, sucesso)
    inicio = time.perf_counter()
    try:
        resposta = enviar_requisicao(payload, *servidor)
        ok = resposta is not None and resposta.get("status") == "success"
    except OSError:
        ok = False
    return time.perf_counter() - inicio, ok


def rodar_single(requisicoes, servidores):
    # Cliente da ASR4: envia uma requisição, espera a resposta e só então envia a próxima
    resultados = []
    for i, req in enumerate(requisicoes):
        resultados.append(enviar_e_medir(req, servidores[i % len(servidores)]))
    return resultados


def rodar_multi(requisicoes, servidores, concorrencia):
    # Cada requisição é enviada por uma thread nova.
    # O semáforo limita quantas threads existem ao mesmo tempo, para não criar milhares de uma vez.
    resultados = [None] * len(requisicoes)
    limite = threading.BoundedSemaphore(concorrencia)

    def trabalhador(i, req, servidor):
        try:
            resultados[i] = enviar_e_medir(req, servidor)
        finally:
            limite.release()

    threads = []
    for i, req in enumerate(requisicoes):
        limite.acquire()
        # Distribui as requisições entre os servidores (round-robin)
        t = threading.Thread(target=trabalhador, args=(i, req, servidores[i % len(servidores)]))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()
    return resultados


def executar_carga(n, modo, servidores, concorrencia=50, seed=None):
    # Gera todas as requisições antes de começar a medir, para o tempo medido ser só envio + processamento + resposta
    rng = random.Random(seed)
    requisicoes = [gerar_requisicao(rng) for _ in range(n)]

    inicio = time.perf_counter()
    if modo == "multi":
        resultados = rodar_multi(requisicoes, servidores, concorrencia)
    else:
        resultados = rodar_single(requisicoes, servidores)
    total = time.perf_counter() - inicio

    latencias = sorted(lat for lat, _ in resultados)
    falhas = sum(1 for _, ok in resultados if not ok)
    return {
        "requisicoes": n,
        "falhas": falhas,
        "tempo_total": total,
        "vazao": n / total,
        "latencia_media": statistics.mean(latencias),
        "latencia_p95": latencias[int(0.95 * (len(latencias) - 1))],
    }


def ler_servidores(texto):
    # Formato: "host:porta,host:porta" (a porta é opcional)
    servidores = []
    for item in texto.split(","):
        host, _, porta = item.strip().partition(":")
        servidores.append((host or HOST, int(porta) if porta else PORT))
    return servidores


def main():
    parser = argparse.ArgumentParser(description="Cliente TCP com geração automática de requisições (ASR5)")
    parser.add_argument("--modo", choices=["single", "multi"], default="multi",
                        help="single = uma requisição por vez; multi = uma thread nova por requisição")
    parser.add_argument("-n", "--requisicoes", type=int, default=1000, help="quantidade de requisições a enviar")
    parser.add_argument("--concorrencia", type=int, default=50, help="máximo de threads enviando ao mesmo tempo (modo multi)")
    parser.add_argument("--servidores", default=f"{HOST}:{PORT}", help="lista host:porta separada por vírgula")
    parser.add_argument("--seed", type=int, default=None, help="semente do gerador aleatório")
    parser.add_argument("--exemplo", action="store_true", help="mostra algumas requisições geradas e as respostas")
    opcoes = parser.parse_args()
    servidores = ler_servidores(opcoes.servidores)

    if opcoes.exemplo:
        rng = random.Random(opcoes.seed)
        for _ in range(5):
            req = gerar_requisicao(rng)
            print("->", json.dumps(req, ensure_ascii=False))
            print("<-", json.dumps(enviar_requisicao(req, *servidores[0]), ensure_ascii=False), "\n")
        return

    print(f"Enviando {opcoes.requisicoes} requisições para {servidores} (cliente {opcoes.modo}-threaded)...")
    r = executar_carga(opcoes.requisicoes, opcoes.modo, servidores, opcoes.concorrencia, opcoes.seed)
    print(f"  Tempo total:     {r['tempo_total']:.3f} s")
    print(f"  Vazão:           {r['vazao']:.1f} req/s")
    print(f"  Latência média:  {r['latencia_media'] * 1000:.2f} ms  (p95: {r['latencia_p95'] * 1000:.2f} ms)")
    print(f"  Falhas:          {r['falhas']}")


if __name__ == "__main__":
    main()
