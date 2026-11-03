from concurrent import futures
import argparse
import logging

import grpc
import text_pb2
import text_pb2_grpc

from const import *
import cliente_nomes



class TextServer(text_pb2_grpc.TextServiceServicer):

    def __init__(self, endereco):
        self.endereco = endereco  # devolvido nas respostas, para o cliente ver quem atendeu

    def Upper(self, request, context):
        print(f" -> maiuscula: {request.text}", flush=True)
        return text_pb2.TextReply(text=request.text.upper(), server=self.endereco)

    def Reverse(self, request, context):
        print(f" -> inverter: {request.text}", flush=True)
        return text_pb2.TextReply(text=request.text[::-1], server=self.endereco)

    def CountWords(self, request, context):
        print(f" -> contar_palavras: {request.text}", flush=True)
        return text_pb2.CountReply(count=len(request.text.split()), server=self.endereco)

    def IsPalindrome(self, request, context):
        print(f" -> palindromo: {request.text}", flush=True)
        # Ignora espaços, pontuação e maiúsculas/minúsculas
        s = "".join(c.lower() for c in request.text if c.isalnum())
        return text_pb2.BoolReply(value=(s == s[::-1]), server=self.endereco)


def main():
    parser = argparse.ArgumentParser(description="Serviço TextService em gRPC (ASR11)")
    parser.add_argument("--porta", type=int, default=50053)
    opcoes = parser.parse_args()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    server.add_insecure_port(f"[::]:{opcoes.porta}")
    # Anuncia o serviço no serviço de nomes antes de começar a atender
    endereco = cliente_nomes.registrar(TEXT_NAME, opcoes.porta)
    text_pb2_grpc.add_TextServiceServicer_to_server(TextServer(endereco), server)
    server.start()

    print("=" * 60)
    print(f"TextService rodando em {endereco} (Ctrl+C para parar)...")
    print("=" * 60, flush=True)

    try:
        # Espera em intervalos de 1 s para o Ctrl+C funcionar também no Windows
        # (wait_for_termination devolve True enquanto o servidor continua no ar)
        while server.wait_for_termination(timeout=1):
            pass
    except KeyboardInterrupt:
        # Sai do serviço de nomes ao encerrar, para ninguém procurar um endereço morto
        cliente_nomes.remover_registro(TEXT_NAME)
        print("\nServidor finalizado pelo usuário.")
    finally:
        server.stop(0)


if __name__ == "__main__":
    logging.basicConfig()
    main()
