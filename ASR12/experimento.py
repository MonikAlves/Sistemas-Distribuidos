import argparse
import importlib.util
import json
import statistics
import sys
import time
from pathlib import Path

import grpc
import requests

# Usa os stubs gerados do exemplo gRPC
PASTA = Path(__file__).parent
sys.path.insert(0, str(PASTA / "grpc"))
import EmployeeService_pb2 as pb
import EmployeeService_pb2_grpc as pb_grpc



def carregar_const(pasta):
    # Os dois exemplos têm um const.py com o mesmo nome; carrega cada um pelo caminho
    # (cada const.py lê o .env da própria pasta)
    spec = importlib.util.spec_from_file_location(f"const_{pasta}", PASTA / pasta / "const.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def medir(descricao, funcao, n):
    # Executa a chamada n vezes em sequência e mostra média, mediana, p95 e vazão
    funcao()  # aquecimento (abre a conexão, etc.)
    tempos = []
    for _ in range(n):
        inicio = time.perf_counter()
        funcao()
        tempos.append((time.perf_counter() - inicio) * 1000)
    tempos.sort()
    media = statistics.mean(tempos)
    print(f"  {descricao:44} n={n:4}  média {media:6.2f} ms  mediana {statistics.median(tempos):6.2f} ms  "
          f"p95 {tempos[int(0.95 * n) - 1]:6.2f} ms  vazão {1000 / media:6.0f} req/s")


def tamanho_http(resposta):
    # Tamanho aproximado da resposta HTTP/1.1: linha de status + cabeçalhos + corpo
    cabecalho = f"HTTP/1.1 {resposta.status_code} {resposta.reason}\r\n"
    cabecalho += "".join(f"{k}: {v}\r\n" for k, v in resposta.headers.items()) + "\r\n"
    return len(cabecalho.encode()), len(resposta.content)


def main():
    parser = argparse.ArgumentParser(description="Experimento de desempenho REST x gRPC (ASR12)")
    parser.add_argument("-n", "--requisicoes", type=int, default=1000, help="chamadas por medição")
    opcoes = parser.parse_args()
    n = opcoes.requisicoes
    const_rest = carregar_const("rest")
    const_grpc = carregar_const("grpc")

    url =f"http://{const_rest.IP_ADD}:{const_rest.PORT}/empdb/employee"
    endereco_grpc = f"{const_grpc.IP}:{const_grpc.PORT}"
    sessao = requests.Session()
    stub = pb_grpc.EmployeeServiceStub(grpc.insecure_channel(endereco_grpc))

    print("=" * 60)
    print(f"REST: {url}")
    print(f"gRPC: {endereco_grpc}")
    print("=" * 60)

    # Rode antes dos clientes originais, porque eles apagam funcionários
    print("\n1) Latência (chamadas sequenciais)")
    medir("REST  GET /employee/201 (conexão nova)", lambda: requests.get(url + "/201").json(), n // 2)
    medir("REST  GET /employee/201 (keep-alive)", lambda: sessao.get(url + "/201").json(), n)
    medir("gRPC  GetEmployeeDataFromID(201)", lambda: stub.GetEmployeeDataFromID(pb.EmployeeID(id=201)), n)
    medir("REST  GET /employee (todos, keep-alive)", lambda: sessao.get(url).json(), n)
    medir("gRPC  ListAllEmployees()", lambda: stub.ListAllEmployees(pb.EmptyMessage()), n)

    print("\n2) Tamanho da resposta")
    casos = [
        ("um funcionário", url + "/201", stub.GetEmployeeDataFromID(pb.EmployeeID(id=201))),
        ("todos", url, stub.ListAllEmployees(pb.EmptyMessage())),
    ]
    for descricao, endereco, msg in casos:
        resposta = sessao.get(endereco)
        cabecalho, corpo = tamanho_http(resposta)
        print(f"  {descricao:15} REST: {corpo:4} B de corpo JSON + {cabecalho:3} B de cabeçalhos HTTP = {corpo + cabecalho:4} B"
              f" | gRPC: {len(msg.SerializeToString()):3} B de payload protobuf (+5 B de framing gRPC)")
        print(f"  {'':15} corpo JSON: {json.dumps(resposta.json(), ensure_ascii=False)}")


if __name__ == "__main__":
    main()
