from concurrent import futures
import logging
import threading

import grpc
import naming_pb2
import naming_pb2_grpc

from const import *



class NamingServer(naming_pb2_grpc.NamingServiceServicer):

    def __init__(self):
        self.registros = {}             # nome -> (ip, porta)
        self.trava = threading.Lock()   # o servidor gRPC atende em várias threads

    def Bind(self, request, context):
        with self.trava:
            if request.name in self.registros:
                context.abort(grpc.StatusCode.ALREADY_EXISTS, f"Nome já registrado: {request.name}")
            self.registros[request.name] = (request.address.ipaddress, request.address.portnumber)
        print(f" -> bind   {request.name} = {request.address.ipaddress}:{request.address.portnumber}", flush=True)
        return naming_pb2.StatusMsg(status="OK")

    def Lookup(self, request, context):
        with self.trava:
            registro = self.registros.get(request.name)
        if registro is None:
            print(f" -> lookup {request.name} = não encontrado", flush=True)
            context.abort(grpc.StatusCode.NOT_FOUND, f"Nome não registrado: {request.name}")
        print(f" -> lookup {request.name} = {registro[0]}:{registro[1]}", flush=True)
        return naming_pb2.AddressMsg(ipaddress=registro[0], portnumber=registro[1])

    def Rebind(self, request, context):
        # Atualiza o endereço; se o nome ainda não existir, cria o registro
        with self.trava:
            existia = request.name in self.registros
            self.registros[request.name] = (request.address.ipaddress, request.address.portnumber)
        print(f" -> rebind {request.name} = {request.address.ipaddress}:{request.address.portnumber}", flush=True)
        return naming_pb2.StatusMsg(status="OK (atualizado)" if existia else "OK (criado)")

    def Unbind(self, request, context):
        with self.trava:
            if request.name not in self.registros:
                context.abort(grpc.StatusCode.NOT_FOUND, f"Nome não registrado: {request.name}")
            del self.registros[request.name]
        print(f" -> unbind {request.name}", flush=True)
        return naming_pb2.StatusMsg(status="OK")

    def List(self, request, context):
        with self.trava:
            itens = sorted(self.registros.items())
        return naming_pb2.BindingList(bindings=[
            naming_pb2.BindMsg(name=nome, address=naming_pb2.AddressMsg(ipaddress=ip, portnumber=porta))
            for nome, (ip, porta) in itens
        ])


def main():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    naming_pb2_grpc.add_NamingServiceServicer_to_server(NamingServer(), server)
    server.add_insecure_port(f"[::]:{NS_PORT}")
    server.start()

    print("=" * 60)
    print(f"Serviço de nomes rodando na porta {NS_PORT}...")
    print("Aguardando bind/lookup/unbind/rebind (Ctrl+C para parar)...")
    print("=" * 60, flush=True)

    try:
        # Espera em intervalos de 1 s para o Ctrl+C funcionar também no Windows
        # (wait_for_termination devolve True enquanto o servidor continua no ar)
        while server.wait_for_termination(timeout=1):
            pass
    except KeyboardInterrupt:
        print("\nServiço de nomes finalizado pelo usuário.")
    finally:
        server.stop(0)


if __name__ == "__main__":
    logging.basicConfig()
    main()
