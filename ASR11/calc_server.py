from concurrent import futures
import argparse
import logging

import grpc
import calculator_pb2
import calculator_pb2_grpc

from const import *
import cliente_nomes



class CalculatorServer(calculator_pb2_grpc.CalculatorServicer):

    def __init__(self, endereco):
        self.endereco = endereco  # devolvido nas respostas, para o cliente ver quem calculou

    def responder(self, op, request, valor):
        print(f" -> {op}({request.a:g}, {request.b:g}) = {valor:g}", flush=True)
        return calculator_pb2.Result(value=valor, server=self.endereco)

    def Add(self, request, context):
        return self.responder("soma", request, request.a + request.b)

    def Subtract(self, request, context):
        return self.responder("subtracao", request, request.a - request.b)

    def Multiply(self, request, context):
        return self.responder("multiplicacao", request, request.a * request.b)

    def Divide(self, request, context):
        # Evita que o servidor quebre com divisão por zero
        if request.b == 0:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Divisão por zero não é permitida")
        return self.responder("divisao", request, request.a / request.b)


def main():
    parser = argparse.ArgumentParser(description="Serviço Calculator em gRPC (ASR11)")
    parser.add_argument("--porta", type=int, default=50052)
    opcoes = parser.parse_args()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    server.add_insecure_port(f"[::]:{opcoes.porta}")
    # Anuncia o serviço no serviço de nomes antes de começar a atender
    endereco = cliente_nomes.registrar(CALC_NAME, opcoes.porta)
    calculator_pb2_grpc.add_CalculatorServicer_to_server(CalculatorServer(endereco), server)
    server.start()

    print("=" * 60)
    print(f"Calculator rodando em {endereco} (Ctrl+C para parar)...")
    print("=" * 60, flush=True)

    try:
        # Espera em intervalos de 1 s para o Ctrl+C funcionar também no Windows
        # (wait_for_termination devolve True enquanto o servidor continua no ar)
        while server.wait_for_termination(timeout=1):
            pass
    except KeyboardInterrupt:
        # Sai do serviço de nomes ao encerrar, para ninguém procurar um endereço morto
        cliente_nomes.remover_registro(CALC_NAME)
        print("\nServidor finalizado pelo usuário.")
    finally:
        server.stop(0)


if __name__ == "__main__":
    logging.basicConfig()
    main()
