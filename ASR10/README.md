# ASR10: ZeroMQ (Req-Rep, Pub-Sub e Pipeline) em máquinas diferentes

**Disciplina:** Sistemas Distribuídos  
**Base:** exemplos das Figs. 4.21, 4.22 e 4.23 do livro do Maarten van Steen (código-fonte fornecido pelo professor na pasta `pacote`)  
**Middleware:** [ZeroMQ](https://zeromq.org/) via `pyzmq`

---

## 1. Os exemplos originais

| Figura | Pasta original | Padrão | O que faz |
|---|---|---|---|
| 4.21 | `pacote/04-22` | Request-Reply (`REQ`/`REP`) | o servidor escuta em 2 portas e devolve a mensagem com `*` |
| 4.22 | `pacote/04-23` | Publish-Subscribe (`PUB`/`SUB`) | o publisher envia a hora a cada 5 s e o subscriber recebe 5 mensagens `TIME` |
| 4.23 | `pacote/04-24` | Pipeline (`PUSH`/`PULL`) | 2 fontes geram tarefas aleatórias e os workers "trabalham" com `sleep` |

O pacote original não está neste repositório. As versões estendidas estão em [reqrep/](reqrep), [pubsub/](pubsub) e [pipeline/](pipeline).

---

## 2. O que foi implementado

### Mudanças comuns aos três

- **Configuração com `.env` e `.env.example`**, como nas ASR4/ASR5. Nos originais o IP ficava fixo no `const*.py`. Agora cada pasta tem um `.env.example`, e o arquivo de constantes lê o `.env` se ele existir ou usa `127.0.0.1` como padrão. As variáveis de ambiente também funcionam.
- **Quem faz `bind` escuta em `tcp://*:porta`** (todas as interfaces). Nos originais o `bind` era no IP privado fixo, e por isso o mesmo arquivo de constantes não servia para as duas máquinas.
- As mensagens mostram **hostname e sistema operacional** de quem respondeu, para ficar claro em qual máquina cada parte rodou.
- **Ctrl+C funciona também no Windows:** os `recv` usam timeout de 1 s (`RCVTIMEO`), mesma ideia do `settimeout` no `accept` da ASR5.

### Req-Rep ([reqrep/](reqrep)): servidor de operações

1. **Processamento no servidor**:
   - As mensagens viraram JSON (`send_json`/`recv_json`) no mesmo formato da ASR4: `{"op": ..., "args": [...]}` -> `{"status": "ok", "result": ...}`.
   - Operações: `maiuscula`, `inverter`, `contar_palavras`, `soma`, `hora`, `operacoes` (lista as operações) e `estatisticas` (quantas requisições de cada tipo já atendeu). Os nomes em inglês (`upper`, `reverse`, `word_count`, `add`, `time`, `ops`, `stats`) também funcionam.
   - **Tratamento de erros:** valor inválido ou operação desconhecida devolve `{"status": "error", ...}` em vez de derrubar o servidor.
   - O `STOP` agora recebe resposta. No original o servidor saía sem responder e o `REQ` do cliente ficava preso.

2. **Cliente**:
   - Conecta nas **duas portas** do servidor, e o socket `REQ` alterna as requisições entre elas (round-robin).
   - Usa **timeout de 5 s** na resposta e mede o tempo de cada requisição.
   - Por padrão roda uma demonstração. Também aceita `--op <operacao> --args ...` e `--stop`.

### Pub-Sub ([pubsub/](pubsub)): vários tópicos

- O publisher publica 3 tópicos: `TIME` (hora), `TEMP` (temperatura aleatória) e `NEWS` (notícia, a cada 3 ciclos).
- Cada mensagem leva um **número de sequência**.
- O subscriber escolhe **quantas mensagens** receber (`-n`) e **quais tópicos** assinar (`--topicos`).
- No fim, o subscriber mostra **mín/máx/média** das temperaturas e quantas **mensagens `TIME` se perderam** (saltos na sequência).
- O intervalo de publicação é configurável (`PS_INTERVALO`, padrão 1 s).

### Pipeline ([pipeline/](pipeline)): sink e trabalho real

- **Novo componente `sink.py`:** coleta os resultados de todos os workers (`PUSH` -> `PULL`), completando o padrão fonte -> workers -> sink.
- O worker faz **trabalho de verdade** no lugar do `sleep`: conta os primos até `carga * 20000` com o crivo de Eratóstenes.
- Cada resultado leva fonte, número da tarefa, worker, máquina, tempo de processamento e tempo total desde a criação da tarefa.
- O sink imprime um **resumo por worker**: quantas tarefas, carga total, de quais fontes recebeu e tempo médio.
- O número de tarefas por fonte é configurável (`PIPE_TAREFAS`, padrão 20). A fonte espera 3 s antes de começar, para os workers conectarem.

---

## 3. Instalação

Em cada máquina:

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip3 install pyzmq
```

No Ubuntu também funciona `sudo apt install python3-zmq`.

---

## 4. Como executar em máquinas diferentes

Em cada pasta, copie o `.env.example` para `.env` e coloque o IP da máquina onde cada parte faz `bind`. Na AWS use o **IP privado** se as instâncias estão na mesma VPC, e libere as portas TCP **4567-4569** no *Security Group* (regra de entrada, origem = o próprio security group ou a VPC).

### Req-Rep

```bash
# máquina A (servidor)
cd reqrep && python3 server.py

# máquina B (cliente), com CS_HOST=<IP_DA_MAQUINA_A> no .env
cd reqrep
python3 client.py                              # demonstração
python3 client.py --op maiuscula --args ola mundo
python3 client.py --stop                       # encerra o servidor
```

### Pub-Sub

```bash
# máquina A (publisher)
cd pubsub && python3 publisher.py

# máquinas B, C, ... (subscribers), com PS_HOST=<IP_DA_MAQUINA_A> no .env
cd pubsub
python3 subscriber.py -n 5 --topicos TIME
python3 subscriber.py -n 8 --topicos TEMP NEWS
```

### Pipeline

```bash
# em TODAS as máquinas, no .env: PIPE_SRC1=<IP_FONTE_1> PIPE_SRC2=<IP_FONTE_2> PIPE_SINK=<IP_SINK>
cd pipeline
python3 sink.py          # na máquina do sink
python3 taskwork.py 1    # worker 1 (qualquer máquina)
python3 taskwork.py 2    # worker 2 (outra máquina)
python3 tasksrc.py 1     # na máquina PIPE_SRC1
python3 tasksrc.py 2     # na máquina PIPE_SRC2
```

---

## 5. Testes realizados

Testei com duas máquinas: **Windows 11** (`172.28.208.1`, Python 3.10 + pyzmq 27.1) e **Ubuntu 22.04 no WSL2** (`172.28.208.130`, Python 3.10 + pyzmq 22.3). O WSL2 é uma VM com IP próprio, então o tráfego passa pela rede entre as duas. As duas máquinas têm o mesmo hostname (`Monik`), por isso a saída mostra o sistema operacional para diferenciar.

### Req-Rep: servidor no Linux, cliente no Windows (`CS_HOST=172.28.208.130`)

```
Servidor: 172.28.208.130:4567 e 172.28.208.130:4568

============================================================
DEMO - TESTES DAS NOVAS FUNCIONALIDADES (REQ-REP)
============================================================

1) Operações disponíveis no servidor
    operacoes() = ['maiuscula', 'inverter', 'contar_palavras', 'soma', 'hora', 'operacoes', 'estatisticas']  [Monik (Linux), 13.70 ms]

2) Manipulação de texto
    maiuscula('hello', 'world') = HELLO WORLD  [Monik (Linux), 0.79 ms]
    inverter('sistemas distribuidos',) = sodiubirtsid sametsis  [Monik (Linux), 0.61 ms]
    contar_palavras('zeromq req rep pub sub pipeline',) = 6  [Monik (Linux), 0.84 ms]

3) Operação matemática
    soma(10, 20, 12.5) = 42.5  [Monik (Linux), 0.63 ms]

4) Utilitário
    hora() = 03/11/2026 10:59:19  [Monik (Linux), 0.62 ms]

5) Tratamento de erros (valor inválido e operação inexistente)
    soma(10, 'abc') = ERRO: Erro de conversão: informe números válidos  [Monik (Linux), 0.53 ms]
    xyz() = ERRO: Operação 'xyz' não reconhecida. Opções: maiuscula, inverter, contar_palavras, soma, hora, operacoes, estatisticas  [Monik (Linux), 0.49 ms]

6) Estatísticas de requisições atendidas
    estatisticas() = {'operacoes': 1, 'maiuscula': 1, 'inverter': 1, 'contar_palavras': 1, 'soma': 2, 'hora': 1, 'xyz': 1}  [Monik (Linux), 0.52 ms]
```

A primeira requisição é mais lenta (13,7 ms) porque inclui o estabelecimento da conexão TCP. As demais ficam abaixo de 1 ms.

Servidor no Linux:

```
============================================================
Servidor REP em Monik (Linux) nas portas 4567 e 4568...
Aguardando requisições (Ctrl+C ou operação STOP para parar)...
============================================================
 -> Requisição recebida: {'op': 'operacoes', 'args': []}
 -> Requisição recebida: {'op': 'maiuscula', 'args': ['hello', 'world']}
 ...
 -> Requisição recebida: {'op': 'STOP', 'args': []}

Servidor finalizado pela operação STOP.
```

Também testei no sentido contrário (servidor no Windows, cliente no Linux com `CS_HOST=172.28.208.1`), e a resposta veio com `[Monik (Windows), ...]`. Com o servidor fora do ar, o cliente mostra `Sem resposta do servidor ... (timeout de 5 s)` em vez de travar.

### Pub-Sub: publisher no Windows, um subscriber em cada máquina

Subscriber no Linux (`PS_HOST=172.28.208.1`, `subscriber.py -n 8 --topicos TEMP NEWS`):

```
Assinando ['TEMP', 'NEWS'] em tcp://172.28.208.1:4567 (8 mensagens)...
 -> [TEMP #3] 17.8
 -> [NEWS #3] AWS: instâncias EC2 conversando via ZeroMQ
 -> [TEMP #4] 23.9
 -> [TEMP #5] 34.5
 -> [TEMP #6] 15.0
 -> [NEWS #6] ZeroMQ desacopla produtores e consumidores
 -> [TEMP #7] 18.3
 -> [TEMP #8] 15.7

============================================================
TEMP: mín 15.0  máx 34.5  média 20.9
============================================================
```

Subscriber no Windows (`subscriber.py -n 5 --topicos TIME`):

```
Assinando ['TIME'] em tcp://127.0.0.1:4567 (5 mensagens)...
 -> [TIME #6] Tue Nov  3 11:00:15 2026
 -> [TIME #7] Tue Nov  3 11:00:16 2026
 -> [TIME #8] Tue Nov  3 11:00:17 2026
 -> [TIME #9] Tue Nov  3 11:00:18 2026
 -> [TIME #10] Tue Nov  3 11:00:19 2026

============================================================
Mensagens TIME perdidas durante a assinatura: 0
============================================================
```

Cada subscriber recebe só os tópicos que assinou (a filtragem é feita pelo ZeroMQ). O número de sequência mostra o problema do *slow joiner*: os subscribers entraram com o publisher já rodando e começaram no #3 e no #6. As mensagens anteriores não foram guardadas para eles, porque o pub-sub do ZeroMQ não tem persistência.

### Pipeline: fontes e workers espalhados

| Componente | Máquina |
|---|---|
| fonte 1, worker 1, sink | Windows (`172.28.208.1`) |
| fonte 2, worker 2 | Linux (`172.28.208.130`) |

Saída do sink (trecho e resumo):

```
============================================================
Sink na porta 4569, esperando 40 resultados...
============================================================
 -> Fonte 2 tarefa  0 -> worker 2@Monik-Linux: 98610 primos (0.019 s de trabalho)
 -> Fonte 1 tarefa  0 -> worker 1@Monik-Windows: 59531 primos (0.016 s de trabalho)
 -> Fonte 2 tarefa  1 -> worker 1@Monik-Windows: 126753 primos (0.030 s de trabalho)
 -> Fonte 1 tarefa  1 -> worker 2@Monik-Linux: 111331 primos (0.034 s de trabalho)
 -> Fonte 2 tarefa  2 -> worker 2@Monik-Linux: 123942 primos (0.037 s de trabalho)
 -> Fonte 2 tarefa  3 -> worker 1@Monik-Windows: 17984 primos (0.006 s de trabalho)
 -> Fonte 1 tarefa  2 -> worker 1@Monik-Windows: 91490 primos (0.028 s de trabalho)
 ...

============================================================
RESUMO
============================================================
1@Monik-Windows      tarefas:  20  carga total:  1091  fontes: ['1', '2']
2@Monik-Linux        tarefas:  20  carga total:  1240  fontes: ['1', '2']
Tempo médio fonte -> resultado: 0.026 s
============================================================
```

Observações:

- As 40 tarefas (20 de cada fonte) chegaram ao sink, e os **dois workers receberam tarefas das duas fontes**, porque cada worker conecta nas duas.
- O `PUSH` distribui as tarefas em **round-robin entre os workers conectados**, por isso cada worker ficou com exatamente 20 tarefas. A *carga* total difere porque cada tarefa tem uma carga aleatória diferente. O round-robin divide pela quantidade de tarefas, não pelo custo delas.
- Em um teste anterior, o worker do Linux conectou alguns segundos depois de as fontes começarem. As primeiras tarefas foram todas para o worker do Windows, e o resultado ficou 25 x 15. Isso acontece porque o `PUSH` só envia para quem já está conectado.

---

## 6. Estrutura

```
ASR10/
├── reqrep/            # constCS.py, server.py, client.py, .env.example
├── pubsub/            # constPS.py, publisher.py, subscriber.py, .env.example
└── pipeline/          # constPipe.py, tasksrc.py, taskwork.py, sink.py, .env.example
```
