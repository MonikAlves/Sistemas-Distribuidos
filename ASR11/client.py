import logging

import grpc
import calculator_pb2
import calculator_pb2_grpc
import text_pb2
import text_pb2_grpc

from const import *
import cliente_nomes



stubs = {}  # cache: nome -> stub já conectado ao endereço descoberto


def obter_stub(nome, classe_stub):
    # O cliente só conhece o serviço de nomes; o endereço do serviço vem do lookup
    if nome not in stubs:
        endereco = cliente_nomes.buscar_endereco(nome)
        print(f"  lookup {nome} -> {endereco}")
        stubs[nome] = classe_stub(grpc.insecure_channel(endereco))
    return stubs[nome]


def chamar(nome, classe_stub, metodo, requisicao):
    # Se o servidor saiu do endereço antigo (UNAVAILABLE), refaz o lookup e tenta de novo
    for tentativa in (1, 2):
        stub = obter_stub(nome, classe_stub)
        try:
            return getattr(stub, metodo)(requisicao, timeout=5)
        except grpc.RpcError as e:
            if e.code() != grpc.StatusCode.UNAVAILABLE or tentativa == 2:
                raise
            print(f"  {nome} indisponível, refazendo lookup...")
            del stubs[nome]


def testar_calculadora():
    print("\n1) Calculator")
    for metodo, a, b in [("Add", 10, 5), ("Subtract", 10, 5), ("Multiply", 6, 7), ("Divide", 22, 7), ("Divide", 1, 0)]:
        try:
            r = chamar(CALC_NAME, calculator_pb2_grpc.CalculatorStub, metodo, calculator_pb2.Operands(a=a, b=b))
            print(f"    {metodo}({a}, {b}) = {r.value:g}   [{r.server}]")
        except grpc.RpcError as e:
            print(f"    {metodo}({a}, {b}) = ERRO {e.code().name}: {e.details()}")


def testar_texto():
    print("\n2) TextService")
    testes = [
        ("Upper", "sistemas distribuidos"),
        ("Reverse", "gRPC naming"),
        ("CountWords", "bind lookup unbind rebind"),
        ("IsPalindrome", "Socorram-me subi no onibus em Marrocos"),
    ]
    for metodo, texto in testes:
        try:
            r = chamar(TEXT_NAME, text_pb2_grpc.TextServiceStub, metodo, text_pb2.TextMsg(text=texto))
            if metodo == "CountWords":
                valor = r.count
            elif metodo == "IsPalindrome":
                valor = r.value
            else:
                valor = r.text
            print(f"    {metodo}('{texto}') = {valor}   [{r.server}]")
        except grpc.RpcError as e:
            print(f"    {metodo}('{texto}') = ERRO {e.code().name}: {e.details()}")


def main():
    print("=" * 60)
    print(f"CLIENTE - serviço de nomes em {NS_HOST}:{NS_PORT}")
    print("=" * 60)

    testar_calculadora()
    testar_texto()

    print("\n" + "=" * 60)
    print("Fim dos testes.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    logging.basicConfig()
    main()
