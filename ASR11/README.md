# ASR11: Serviço de Nomes e serviços de aplicação em gRPC

**Disciplina:** Sistemas Distribuídos  
**Base:** [professorfabio/gRPC-SimpleNamingService](https://github.com/professorfabio/gRPC-SimpleNamingService)  
**Referência:** [gRPC Python Quickstart](https://grpc.io/docs/languages/python/quickstart/)

---

## 1. Arquitetura

```
                       ┌─────────────────────────┐
          bind/rebind  │  Serviço de Nomes       │  lookup
       ┌──────────────►│  naming_server.py       │◄──────────────┐
       │   unbind      │  porta 50051            │               │
       │               └─────────────────────────┘               │
       │                                                         │
┌──────┴───────────┐   ┌──────────────────┐             ┌───────┴──────┐
│ calc_server.py   │   │ text_server.py   │◄────────────│  client.py   │
│ "Calculator"     │◄──┼──────────────────┼─────────────│              │
│ porta 50052      │   │ "TextService"    │  chamadas   └──────────────┘
└──────────────────┘   │ porta 50053      │  gRPC diretas
     máquina A         └──────────────────┘
                            máquina B
```

- O **único endereço fixo** que servidores e cliente conhecem é o do serviço de nomes (`NS_HOST`/`NS_PORT` no `.env`).
- Ao iniciar, cada servidor de aplicação **se registra** com seu nome lógico e o endereço onde escuta.
- O cliente faz **lookup** pelo nome e então chama o serviço **diretamente** (o serviço de nomes não fica no caminho das chamadas).
- Tudo é gRPC: o serviço de nomes e os dois serviços têm contrato em `.proto` ([protos/](protos)).

---

## 2. Serviço de Nomes ([naming_server.py](naming_server.py))

Contrato em [protos/naming.proto](protos/naming.proto):

| RPC | Uso | Sucesso | Erro |
|---|---|---|---|
| `Bind(name, address)` | servidor registra nome e endereço | `OK` | `ALREADY_EXISTS` se o nome já existe |
| `Lookup(name)` | cliente descobre o endereço | `AddressMsg(ip, porta)` | `NOT_FOUND` |
| `Unbind(name)` | remove o registro | `OK` | `NOT_FOUND` |
| `Rebind(name, address)` | atualiza o endereço (cria se não existir) | `OK (atualizado)` / `OK (criado)` | n/a |
| `List()` | lista todos os registros (extra, para depuração) | `BindingList` | n/a |

Diferenças em relação ao exemplo de referência:

- Os registros ficam em um **dicionário protegido por `Lock`**, porque o servidor gRPC atende requisições em várias threads (`ThreadPoolExecutor`).
- Os erros usam **códigos de status do gRPC** (`ALREADY_EXISTS`, `NOT_FOUND`) em vez de strings vazias. No exemplo original, o `Lookup` de um nome inexistente devolvia IP vazio, o `Rebind` de um nome inexistente quebrava com `IndexError` e o `Bind` aceitava nomes duplicados.

---

## 3. Serviços de aplicação

| Nome lógico | Arquivo | Contrato | Operações |
|---|---|---|---|
| `Calculator` | [calc_server.py](calc_server.py) | [calculator.proto](protos/calculator.proto) | `Add`, `Subtract`, `Multiply`, `Divide` (divisão por zero -> `INVALID_ARGUMENT`) |
| `TextService` | [text_server.py](text_server.py) | [text.proto](protos/text.proto) | `Upper`, `Reverse`, `CountWords`, `IsPalindrome` |

Cada resposta inclui o campo `server` (`ip:porta` de quem respondeu), para o cliente ver qual instância atendeu.

Ciclo de vida de um servidor (funções em [cliente_nomes.py](cliente_nomes.py)):

1. **`descobrir_meu_ip()`:** usa o IP da interface que alcança o serviço de nomes, ou o `APP_HOST` do `.env` se estiver preenchido (útil na AWS para anunciar o IP público).
2. **`registrar()`:** faz `Bind`. Se o nome já existe (`ALREADY_EXISTS`), por exemplo porque uma instância anterior caiu sem se desregistrar, faz `Rebind` com o endereço novo.
3. **`remover_registro()`:** ao receber **Ctrl+C**, o servidor faz `Unbind` antes de encerrar.

---

## 4. Cliente ([client.py](client.py))

- `obter_stub()` faz o `Lookup` de `Calculator` e `TextService` e guarda em cache o stub de cada um.
- `chamar()` trata o caso de uma chamada falhar com **`UNAVAILABLE`** (o servidor saiu daquele endereço): o cliente **descarta o cache, refaz o `Lookup`** e tenta de novo. Assim ele acompanha um `Rebind` sem precisar reiniciar.
- Trata `NOT_FOUND` (serviço não registrado) e `INVALID_ARGUMENT` (divisão por zero) sem quebrar.

O [teste_nomes.py](teste_nomes.py) testa as quatro funções do serviço de nomes, inclusive os casos de erro, no estilo do `testNS.py` original.

---

## 5. Como executar

### Instalação (em cada máquina)

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

As versões do `requirements.txt` (grpcio 1.85 e protobuf 7) exigem **Python 3.10 ou mais novo**. No Amazon Linux 2023, cujo Python padrão é o 3.9, instale o 3.11:

```bash
sudo dnf install -y python3.11 python3.11-pip
python3.11 -m pip install --user -r requirements.txt
```

### Configuração

Copie o `.env.example` para `.env` e coloque o IP da máquina do serviço de nomes:

```
NS_HOST=<IP_DO_SERVICO_DE_NOMES>
NS_PORT=50051
APP_HOST=
```

### Gerar os stubs (só se alterar os `.proto`)

Os arquivos `*_pb2.py` e `*_pb2_grpc.py` já estão no repositório, gerados com as versões do `requirements.txt`.

```bash
python -m grpc_tools.protoc -Iprotos --python_out=. --grpc_python_out=. protos/naming.proto protos/calculator.proto protos/text.proto
```

### Executar

```bash
python naming_server.py              # máquina do serviço de nomes
python calc_server.py --porta 50052  # máquina A
python text_server.py --porta 50053  # máquina B
python client.py                     # cliente (qualquer máquina)
python teste_nomes.py                # testa bind/lookup/rebind/unbind
```

Na AWS, libere as portas TCP 50051-50054 no Security Group.

---

## 6. Testes na AWS (EC2)

Usei as mesmas duas instâncias da [ASR10](../ASR10/README.md#5-testes-na-aws-ec2): t3.micro com Amazon Linux 2023, região `us-east-1`. Instalei Python 3.11 com grpcio 1.85.1 e protobuf 7.36.2 e liberei as portas 50051-50054 só entre as instâncias do Security Group.

| Processo | Máquina |
|---|---|
| Serviço de nomes (`:50051`) | A (`172.31.24.5`) |
| `Calculator` (`:50052`) | A (`172.31.24.5`) |
| `TextService` (`:50053`) | B (`172.31.29.134`) |
| Cliente e `teste_nomes.py` | B (`172.31.29.134`) |

### Testes 1 e 2: cliente na B descobre os serviços e testa o serviço de nomes

```
============================================================
CLIENTE - serviço de nomes em 172.31.24.5:50051
============================================================

1) Calculator
  lookup Calculator -> 172.31.24.5:50052
    Add(10, 5) = 15   [172.31.24.5:50052]
    Subtract(10, 5) = 5   [172.31.24.5:50052]
    Multiply(6, 7) = 42   [172.31.24.5:50052]
    Divide(22, 7) = 3.14286   [172.31.24.5:50052]
    Divide(1, 0) = ERRO INVALID_ARGUMENT: Divisão por zero não é permitida

2) TextService
  lookup TextService -> 172.31.29.134:50053
    Upper('sistemas distribuidos') = SISTEMAS DISTRIBUIDOS   [172.31.29.134:50053]
    Reverse('gRPC naming') = gniman CPRg   [172.31.29.134:50053]
    CountWords('bind lookup unbind rebind') = 4   [172.31.29.134:50053]
    IsPalindrome('Socorram-me subi no onibus em Marrocos') = True   [172.31.29.134:50053]

============================================================
Fim dos testes.
============================================================

============================================================
TESTE DO SERVIÇO DE NOMES
============================================================
  bind TesteSvc 10.0.0.1:6000      -> OK
  bind TesteSvc (de novo)          -> ERRO ALREADY_EXISTS: Nome já registrado: TesteSvc
  lookup TesteSvc                  -> 10.0.0.1:6000
  rebind TesteSvc 10.0.0.2:6001    -> OK (atualizado)
  lookup TesteSvc                  -> 10.0.0.2:6001
  unbind TesteSvc                  -> OK
  lookup TesteSvc                  -> ERRO NOT_FOUND: Nome não registrado: TesteSvc
  unbind TesteSvc (de novo)        -> ERRO NOT_FOUND: Nome não registrado: TesteSvc

Registros atuais:
  Calculator   172.31.24.5:50052
  TextService  172.31.29.134:50053
```

Cada servidor descobriu sozinho o próprio IP privado (o da interface que alcança o serviço de nomes) e se registrou com ele.

### Testes 3 e 4: unbind ao encerrar e servidor mudando de máquina

1. O `Calculator` na A recebeu SIGINT (Ctrl+C, via `timeout -s INT`) e saiu do serviço de nomes.
2. Um cliente na B fez a 1ª chamada ao `TextService` da B e ficou esperando.
3. O `TextService` da B foi morto com `kill -9` (sem `Unbind`).
4. Um novo `TextService` subiu na **A, porta 50054**, e fez `Rebind`.
5. A 2ª chamada do cliente encontrou o endereço antigo fora do ar, refez o lookup e foi atendida na A.

Cliente da troca (máquina B):

```
  lookup TextService -> 172.31.29.134:50053
1a chamada: ANTES DA TROCA [172.31.29.134:50053]
  TextService indisponível, refazendo lookup...
  lookup TextService -> 172.31.24.5:50054
2a chamada: DEPOIS DA TROCA [172.31.24.5:50054]
```

`client.py` rodado depois (máquina B):

```
1) Calculator
    Add(10, 5) = ERRO NOT_FOUND: Nome não registrado: Calculator
    Subtract(10, 5) = ERRO NOT_FOUND: Nome não registrado: Calculator
    Multiply(6, 7) = ERRO NOT_FOUND: Nome não registrado: Calculator
    Divide(22, 7) = ERRO NOT_FOUND: Nome não registrado: Calculator
    Divide(1, 0) = ERRO NOT_FOUND: Nome não registrado: Calculator

2) TextService
  lookup TextService -> 172.31.24.5:50054
    Upper('sistemas distribuidos') = SISTEMAS DISTRIBUIDOS   [172.31.24.5:50054]
    ...
```

Logs da máquina A (fim do `Calculator`, novo `TextService` e serviço de nomes):

```
 -> divisao(22, 7) = 3.14286
unbind Calculator : OK

Servidor finalizado pelo usuário.

rebind TextService -> 172.31.24.5:50054 : OK (atualizado)
============================================================
TextService rodando em 172.31.24.5:50054 (Ctrl+C para parar)...
============================================================
 -> maiuscula: depois da troca
 -> maiuscula: sistemas distribuidos
 -> inverter: gRPC naming
 -> contar_palavras: bind lookup unbind rebind
 -> palindromo: Socorram-me subi no onibus em Marrocos

============================================================
Serviço de nomes rodando na porta 50051...
Aguardando bind/lookup/unbind/rebind (Ctrl+C para parar)...
============================================================
 -> bind   Calculator = 172.31.24.5:50052
 -> bind   TextService = 172.31.29.134:50053
 -> lookup Calculator = 172.31.24.5:50052
 -> lookup TextService = 172.31.29.134:50053
 -> bind   TesteSvc = 10.0.0.1:6000
 -> lookup TesteSvc = 10.0.0.1:6000
 -> rebind TesteSvc = 10.0.0.2:6001
 -> lookup TesteSvc = 10.0.0.2:6001
 -> unbind TesteSvc
 -> lookup TesteSvc = não encontrado
 -> unbind Calculator
 -> lookup TextService = 172.31.29.134:50053
 -> rebind TextService = 172.31.24.5:50054
 -> lookup TextService = 172.31.24.5:50054
 -> lookup Calculator = não encontrado
 ...
 -> lookup TextService = 172.31.24.5:50054
```

Ao fim dos testes, as instâncias foram paradas para não consumir créditos.

---

## 7. Testes em máquinas locais (Windows + WSL2)

Antes da AWS, usei duas máquinas locais: **Windows 11** (`172.28.208.1`) e **Ubuntu 22.04 no WSL2** (`172.28.208.130`, uma VM com IP próprio), com Python 3.10, grpcio 1.85.1 e protobuf 7.36.2 nas duas.

| Processo | Máquina |
|---|---|
| Serviço de nomes (`:50051`) | Windows |
| `TextService` (`:50053`) | Windows |
| `Calculator` (`:50052`) | Linux |
| Cliente | Linux |

### Teste 1: cliente no Linux descobre os dois serviços

Servidores ao subir:

```
bind TextService -> 172.28.208.1:50053 : OK         (Windows)
bind Calculator -> 172.28.208.130:50052 : OK        (Linux)
```

Cliente (`NS_HOST=172.28.208.1`):

```
============================================================
CLIENTE - serviço de nomes em 172.28.208.1:50051
============================================================

1) Calculator
  lookup Calculator -> 172.28.208.130:50052
    Add(10, 5) = 15   [172.28.208.130:50052]
    Subtract(10, 5) = 5   [172.28.208.130:50052]
    Multiply(6, 7) = 42   [172.28.208.130:50052]
    Divide(22, 7) = 3.14286   [172.28.208.130:50052]
    Divide(1, 0) = ERRO INVALID_ARGUMENT: Divisão por zero não é permitida

2) TextService
  lookup TextService -> 172.28.208.1:50053
    Upper('sistemas distribuidos') = SISTEMAS DISTRIBUIDOS   [172.28.208.1:50053]
    Reverse('gRPC naming') = gniman CPRg   [172.28.208.1:50053]
    CountWords('bind lookup unbind rebind') = 4   [172.28.208.1:50053]
    IsPalindrome('Socorram-me subi no onibus em Marrocos') = True   [172.28.208.1:50053]
```

### Teste 2: as quatro funções do serviço de nomes (`teste_nomes.py`)

```
============================================================
TESTE DO SERVIÇO DE NOMES
============================================================
  bind TesteSvc 10.0.0.1:6000      -> OK
  bind TesteSvc (de novo)          -> ERRO ALREADY_EXISTS: Nome já registrado: TesteSvc
  lookup TesteSvc                  -> 10.0.0.1:6000
  rebind TesteSvc 10.0.0.2:6001    -> OK (atualizado)
  lookup TesteSvc                  -> 10.0.0.2:6001
  unbind TesteSvc                  -> OK
  lookup TesteSvc                  -> ERRO NOT_FOUND: Nome não registrado: TesteSvc
  unbind TesteSvc (de novo)        -> ERRO NOT_FOUND: Nome não registrado: TesteSvc

Registros atuais:
  Calculator   172.28.208.130:50052
  TextService  172.28.208.1:50053
```

### Teste 3: unbind ao encerrar

Encerrei o `Calculator` com Ctrl+C (SIGINT):

```
unbind Calculator : OK

Servidor finalizado pelo usuário.
```

Depois disso, o cliente recebe `NOT_FOUND` em vez de tentar um endereço morto:

```
1) Calculator
    Add(10, 5) = ERRO NOT_FOUND: Nome não registrado: Calculator
    Subtract(10, 5) = ERRO NOT_FOUND: Nome não registrado: Calculator
    ...
```

### Teste 4: servidor muda de máquina (rebind) e o cliente acompanha

1. Um cliente no Windows faz a 1ª chamada ao `TextService` (endereço `172.28.208.1:50053` em cache) e espera 25 s.
2. Enquanto isso, o `TextService` do Windows é **morto à força** (sem `Unbind`, simulando uma falha).
3. Um novo `TextService` sobe no **Linux, porta 50054**. O `Bind` falha com `ALREADY_EXISTS` (registro antigo ainda lá), então o servidor faz `Rebind`:

   ```
   rebind TextService -> 172.28.208.130:50054 : OK (atualizado)
   ============================================================
   TextService rodando em 172.28.208.130:50054 (Ctrl+C para parar)...
   ============================================================
   ```

4. O cliente faz a 2ª chamada. O endereço antigo está fora do ar (`UNAVAILABLE`), então ele refaz o lookup e é atendido pela nova instância:

   ```
     lookup TextService -> 172.28.208.1:50053
   1a chamada: ANTES DA TROCA [172.28.208.1:50053]
     TextService indisponível, refazendo lookup...
     lookup TextService -> 172.28.208.130:50054
   2a chamada: DEPOIS DA TROCA [172.28.208.130:50054]
   ```

Log do serviço de nomes durante todos os testes:

```
============================================================
Serviço de nomes rodando na porta 50051...
Aguardando bind/lookup/unbind/rebind (Ctrl+C para parar)...
============================================================
 -> bind   TextService = 172.28.208.1:50053
 -> bind   Calculator = 172.28.208.130:50052
 -> lookup Calculator = 172.28.208.130:50052
 -> lookup TextService = 172.28.208.1:50053
 -> bind   TesteSvc = 10.0.0.1:6000
 -> lookup TesteSvc = 10.0.0.1:6000
 -> rebind TesteSvc = 10.0.0.2:6001
 -> lookup TesteSvc = 10.0.0.2:6001
 -> unbind TesteSvc
 -> lookup TesteSvc = não encontrado
 -> lookup TextService = 172.28.208.1:50053
 -> unbind Calculator
 -> rebind TextService = 172.28.208.130:50054
 -> lookup TextService = 172.28.208.130:50054
 -> lookup Calculator = não encontrado
 ...
```

---

## 8. Estrutura

```
ASR11/
├── protos/
│   ├── naming.proto
│   ├── calculator.proto
│   └── text.proto
├── naming_server.py      # serviço de nomes
├── calc_server.py        # serviço de aplicação 1
├── text_server.py        # serviço de aplicação 2
├── client.py             # cliente: lookup + chamadas
├── cliente_nomes.py      # registrar/remover_registro/buscar_endereco (usado por todos)
├── teste_nomes.py        # teste das funções do serviço de nomes
├── const.py              # lê o .env: endereço do serviço de nomes e nomes lógicos
├── .env.example
├── *_pb2.py, *_pb2_grpc.py  # gerados pelo grpc_tools.protoc
└── requirements.txt
```
