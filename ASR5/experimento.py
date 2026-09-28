import argparse
import platform
import os
import socket
import statistics
import subprocess
import sys
import time
from pathlib import Path

from client import executar_carga



PASTA = Path(__file__).parent
HOST = "127.0.0.1"

# (nome, modo do cliente, modo do servidor, quantidade de servidores)
CONFIGURACOES = [
    ("A. Cliente single + servidor single (ASR4)",  "single", "single", 1),
    ("B. Cliente single + servidor multi",           "single", "multi",  1),
    ("C. Cliente multi + servidor multi",            "multi",  "multi",  1),
    ("D. Cliente multi + servidor single",           "multi",  "single", 1),
    ("E. Cliente multi + 2 servidores multi",        "multi",  "multi",  2),
]


def esperar_porta(porta, limite=10.0):
    fim = time.time() + limite
    while time.time() < fim:
        try:
            with socket.create_connection((HOST, porta), timeout=0.5):
                return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError(f"Servidor na porta {porta} não subiu")


def subir_servidores(modo, quantidade, porta_base, atraso):
    processos = []
    for i in range(quantidade):
        porta = porta_base + i
        cmd = [sys.executable, str(PASTA / "server.py"), "--modo", modo, "--porta", str(porta),
               "--atraso", str(atraso), "--quiet"]
        processos.append(subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
        esperar_porta(porta)
    return processos


def derrubar_servidores(processos):
    for p in processos:
        p.terminate()
    for p in processos:
        p.wait()


def main():
    parser = argparse.ArgumentParser(description="Experimento de desempenho ASR5")
    parser.add_argument("-n", "--requisicoes", type=int, default=1000)
    parser.add_argument("--repeticoes", type=int, default=3)
    parser.add_argument("--concorrencia", type=int, default=50)
    parser.add_argument("--atrasos", default="0,10", help="atrasos simulados no servidor (ms), separados por vírgula")
    parser.add_argument("--porta", type=int, default=6000)
    parser.add_argument("--saida", default=str(PASTA / "resultados.md"))
    opcoes = parser.parse_args()
    atrasos = [float(a) for a in opcoes.atrasos.split(",")]

    linhas = [
        "# Resultados do experimento",
        "",
        f"- Máquina: {platform.platform()}, {os.cpu_count()} CPUs lógicas, Python {platform.python_version()}",
        f"- Cliente e servidores na mesma máquina ({HOST})",
        f"- {opcoes.requisicoes} requisições por execução, {opcoes.repeticoes} repetições por configuração "
        f"(mesma semente aleatória em todas), até {opcoes.concorrencia} threads simultâneas no cliente multi",
        "",
    ]

    porta = opcoes.porta
    for atraso in atrasos:
        print(f"\n=== Atraso simulado no servidor: {atraso:g} ms ===")
        linhas += [
            f"## Atraso simulado no servidor: {atraso:g} ms por requisição",
            "",
            "| Configuração | Tempo total (s) | Vazão (req/s) | Latência média (ms) | Latência p95 (ms) | Speedup vs A | Falhas |",
            "|---|---|---|---|---|---|---|",
        ]
        tempo_base = None

        for nome, modo_cliente, modo_servidor, qtd in CONFIGURACOES:
            # Porta nova a cada configuração, para não reaproveitar conexões em TIME_WAIT
            processos = subir_servidores(modo_servidor, qtd, porta, atraso)
            servidores = [(HOST, porta + i) for i in range(qtd)]
            porta += qtd
            try:
                medidas = [executar_carga(opcoes.requisicoes, modo_cliente, servidores, opcoes.concorrencia, seed=42 + r)
                           for r in range(opcoes.repeticoes)]
            finally:
                derrubar_servidores(processos)

            tempos = [m["tempo_total"] for m in medidas]
            tempo = statistics.mean(tempos)
            desvio = statistics.stdev(tempos) if len(tempos) > 1 else 0.0
            if tempo_base is None:
                tempo_base = tempo
            vazao = opcoes.requisicoes / tempo
            lat = statistics.mean(m["latencia_media"] for m in medidas) * 1000
            p95 = statistics.mean(m["latencia_p95"] for m in medidas) * 1000
            falhas = sum(m["falhas"] for m in medidas)

            print(f"{nome:45s} {tempo:8.3f} s ± {desvio:.3f}  {vazao:9.1f} req/s  speedup {tempo_base / tempo:5.2f}x  falhas {falhas}")
            linhas.append(f"| {nome} | {tempo:.3f} ± {desvio:.3f} | {vazao:.1f} | {lat:.2f} | {p95:.2f} | "
                          f"{tempo_base / tempo:.2f}x | {falhas} |")
        linhas.append("")

    Path(opcoes.saida).write_text("\n".join(linhas), encoding="utf-8")
    print(f"\nTabela salva em {opcoes.saida}")


if __name__ == "__main__":
    main()
