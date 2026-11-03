# Funções de acesso ao serviço de nomes, usadas pelos servidores e pelo cliente
import socket

import grpc
import naming_pb2
import naming_pb2_grpc

from const import *



def conectar_servico_nomes():
    canal = grpc.insecure_channel(f"{NS_HOST}:{NS_PORT}")
    return naming_pb2_grpc.NamingServiceStub(canal)


def descobrir_meu_ip():
    # APP_HOST permite forçar o IP anunciado (ex.: IP público na AWS).
    # Sem ele, usa o IP da interface que alcança o serviço de nomes.
    if APP_HOST:
        return APP_HOST
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect((NS_HOST, NS_PORT))  # UDP: não envia nada, só escolhe a interface
        return s.getsockname()[0]
    finally:
        s.close()


def registrar(nome, porta):
    # Tenta bind; se o nome já existe (ex.: servidor reiniciou em outro lugar), faz rebind
    stub = conectar_servico_nomes()
    endereco = naming_pb2.AddressMsg(ipaddress=descobrir_meu_ip(), portnumber=str(porta))
    msg = naming_pb2.BindMsg(name=nome, address=endereco)
    try:
        status = stub.Bind(msg).status
        operacao = "bind"
    except grpc.RpcError as e:
        if e.code() != grpc.StatusCode.ALREADY_EXISTS:
            raise
        status = stub.Rebind(msg).status
        operacao = "rebind"
    print(f"{operacao} {nome} -> {endereco.ipaddress}:{endereco.portnumber} : {status}", flush=True)
    return f"{endereco.ipaddress}:{endereco.portnumber}"


def remover_registro(nome):
    try:
        status = conectar_servico_nomes().Unbind(naming_pb2.NameMsg(name=nome)).status
        print(f"unbind {nome} : {status}")
    except grpc.RpcError as e:
        print(f"unbind {nome} : {e.details()}")


def buscar_endereco(nome):
    # Um nome não registrado gera grpc.RpcError com código NOT_FOUND
    resposta = conectar_servico_nomes().Lookup(naming_pb2.NameMsg(name=nome))
    return f"{resposta.ipaddress}:{resposta.portnumber}"
