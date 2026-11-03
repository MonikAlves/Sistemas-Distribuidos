# Testa as quatro funções do serviço de nomes (inclusive os casos de erro),
# no mesmo estilo do testNS.py do repositório de referência
import logging

import grpc
import naming_pb2

import cliente_nomes



def exibir(descricao, funcao):
    try:
        r = funcao()
        if isinstance(r, naming_pb2.AddressMsg):
            print(f"  {descricao:32} -> {r.ipaddress}:{r.portnumber}")
        else:
            print(f"  {descricao:32} -> {r.status}")
    except grpc.RpcError as e:
        print(f"  {descricao:32} -> ERRO {e.code().name}: {e.details()}")


def main():
    stub = cliente_nomes.conectar_servico_nomes()
    end1 = naming_pb2.AddressMsg(ipaddress="10.0.0.1", portnumber="6000")
    end2 = naming_pb2.AddressMsg(ipaddress="10.0.0.2", portnumber="6001")
    nome = naming_pb2.NameMsg(name="TesteSvc")

    print("=" * 60)
    print("TESTE DO SERVIÇO DE NOMES")
    print("=" * 60)

    exibir("bind TesteSvc 10.0.0.1:6000",   lambda: stub.Bind(naming_pb2.BindMsg(name="TesteSvc", address=end1)))
    exibir("bind TesteSvc (de novo)",       lambda: stub.Bind(naming_pb2.BindMsg(name="TesteSvc", address=end2)))
    exibir("lookup TesteSvc",               lambda: stub.Lookup(nome))
    exibir("rebind TesteSvc 10.0.0.2:6001", lambda: stub.Rebind(naming_pb2.BindMsg(name="TesteSvc", address=end2)))
    exibir("lookup TesteSvc",               lambda: stub.Lookup(nome))
    exibir("unbind TesteSvc",               lambda: stub.Unbind(nome))
    exibir("lookup TesteSvc",               lambda: stub.Lookup(nome))
    exibir("unbind TesteSvc (de novo)",     lambda: stub.Unbind(nome))

    print("\nRegistros atuais:")
    for b in stub.List(naming_pb2.Empty()).bindings:
        print(f"  {b.name:12} {b.address.ipaddress}:{b.address.portnumber}")


if __name__ == "__main__":
    logging.basicConfig()
    main()
