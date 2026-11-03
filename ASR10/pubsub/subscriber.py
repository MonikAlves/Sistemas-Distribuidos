import zmq
from constPS import * #-
import argparse



def receber_mensagens(s, n):
    temperaturas = []
    ultimo_seq = None
    perdidas = 0

    recebidas = 0
    while recebidas < n:
        try:
            msg = s.recv_string()
        except zmq.Again:
            continue
        recebidas += 1
        topico, seq, conteudo = msg.split(" ", 2)
        seq = int(seq)
        print(f" -> [{topico} #{seq}] {conteudo}", flush=True)

        if topico == "TIME":
            # Um salto na sequência indica mensagens TIME que não chegaram
            if ultimo_seq is not None and seq != ultimo_seq + 1:
                perdidas += seq - ultimo_seq - 1
            ultimo_seq = seq
        elif topico == "TEMP":
            temperaturas.append(float(conteudo))

    return temperaturas, perdidas


def exibir_resumo(topicos, temperaturas, perdidas):
    print("\n" + "=" * 60)
    if temperaturas:
        media = sum(temperaturas) / len(temperaturas)
        print(f"TEMP: mín {min(temperaturas):.1f}  máx {max(temperaturas):.1f}  média {media:.1f}")
    if "TIME" in topicos:
        print(f"Mensagens TIME perdidas durante a assinatura: {perdidas}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Subscriber ZeroMQ SUB (ASR10)")
    parser.add_argument("-n", "--mensagens", type=int, default=5, help="quantidade de mensagens a receber")
    parser.add_argument("--topicos", nargs="+", default=["TIME"], help="tópicos assinados: TIME, TEMP e/ou NEWS")
    opcoes = parser.parse_args()

    context = zmq.Context()
    # Socket assinante (SUB), conectado ao publisher
    s = context.socket(zmq.SUB)
    s.connect(f"tcp://{HOST}:{PORT}")
    for topico in opcoes.topicos:
        s.setsockopt_string(zmq.SUBSCRIBE, topico)
    # Timeout no recv para o Ctrl+C funcionar também no Windows
    s.setsockopt(zmq.RCVTIMEO, 1000)

    print(f"Assinando {opcoes.topicos} em tcp://{HOST}:{PORT} ({opcoes.mensagens} mensagens)...", flush=True)

    try:
        temperaturas, perdidas = receber_mensagens(s, opcoes.mensagens)
        exibir_resumo(opcoes.topicos, temperaturas, perdidas)
    except KeyboardInterrupt:
        print("\nSubscriber finalizado pelo usuário.")
    finally:
        s.close(linger=0)
        context.term()


if __name__ == "__main__":
    main()
