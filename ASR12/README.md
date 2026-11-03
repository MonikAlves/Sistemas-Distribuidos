# ASR12: Comparação entre RESTful e gRPC

**Disciplina:** Sistemas Distribuídos  
**Base:** [professorfabio/RESTful-WS-Example](https://github.com/professorfabio/RESTful-WS-Example) e [professorfabio/gRPC-WS-Example](https://github.com/professorfabio/gRPC-WS-Example)

Os dois exemplos implementam o mesmo serviço de funcionários (`EmployeeService`): listar, consultar, criar, alterar e remover funcionários. As cópias estão em [rest/](rest) e [grpc/](grpc), sem alterações no código. Mudei só o `const.py` de cada um, que agora lê o IP do `.env` (com `.env.example`, como nas ASR4/ASR5) em vez de deixar fixo. O [experimento.py](experimento.py) mede latência e tamanho das mensagens nos dois.

---

## 1. Como executar

```bash
pip install flask requests grpcio grpcio-tools

# servidor (máquina A)
cd rest && python EmployeeService.py          # porta 5678
cd grpc && python EmployeeService.py          # porta 50051

# cliente (máquina B): em rest/.env coloque REST_HOST=<IP_A> e em grpc/.env GRPC_HOST=<IP_A>
python experimento.py -n 1000                 # rode antes dos clientes, que apagam registros
cd rest && python EmployeeServiceClient.py
cd grpc && python EmployeeClient.py
```

Para regerar os stubs gRPC: `cd grpc && python -m grpc_tools.protoc -Iprotos --python_out=. --grpc_python_out=. protos/EmployeeService.proto`

---

## 2. Modelo de programação

| | RESTful (Flask + requests) | gRPC |
|---|---|---|
| **Abstração** | **recursos** identificados por URL (`/empdb/employee/201`) manipulados por uma **interface genérica e uniforme**: os verbos HTTP `GET`, `POST`, `PUT`, `DELETE` | **procedimentos remotos** específicos da aplicação (`GetEmployeeDataFromID`, `UpdateEmployeeTitle`...), chamados como métodos de um objeto local (stub) |
| **Contrato** | implícito: a URL, o verbo e o formato do JSON estão só no código e na documentação. Nada obriga cliente e servidor a concordarem | explícito: [EmployeeService.proto](grpc/protos/EmployeeService.proto) define serviços, métodos e tipos das mensagens |
| **Código de comunicação** | o programador monta a URL, escolhe o verbo, serializa e lê o JSON (`requests.put(url, json=update)`, `response.json()`) | gerado pelo `protoc` (`*_pb2.py`, `*_pb2_grpc.py`). O cliente faz `stub.GetEmployeeDataFromID(EmployeeID(id=101))` |
| **Tipos** | dinâmicos: no exemplo, `id` e `salary` são strings, e qualquer campo extra ou faltando passa | estáticos: `uint32 id`. Passar `id=-1` falha **no cliente**, antes de sair da máquina (`ValueError: Value out of range: -1`) |
| **Transporte e formato** | HTTP/1.1 + JSON (texto) | HTTP/2 + Protocol Buffers (binário) |
| **Erros** | código de status HTTP (`404`, `500`) + corpo livre | códigos de status gRPC (`NOT_FOUND`, `INVALID_ARGUMENT`...) + mensagem |

A diferença central é **interface genérica x interface específica de aplicação**. No REST o vocabulário de operações é fixo (os verbos do HTTP), e a aplicação define *recursos*. Isso explica o endpoint estranho `PUT /empdb/employee/<id>/<salario>`, que tenta encaixar a operação "alterar salário" no modelo de recursos. No gRPC cada operação vira um método com nome e tipos próprios (`UpdateEmployeeTitle(EmployeeTitleUpdate)`), mais próximo da forma como o programador pensa no código.

---

## 3. Resultados dos testes

Servidores no **Ubuntu 22.04 (WSL2, `172.28.208.130`)**, cliente no **Windows 11**, Python 3.10, Flask 3.1.3 (servidor de desenvolvimento Werkzeug), grpcio 1.85.1. 1000 chamadas sequenciais por linha (500 na de conexão nova).

### Latência entre as duas máquinas (Windows -> Linux)

| Operação | Média | Mediana | p95 | Vazão |
|---|---|---|---|---|
| REST `GET /employee/201` (conexão nova a cada chamada) | 15,15 ms | 15,02 ms | 16,39 ms | 66 req/s |
| REST `GET /employee/201` (keep-alive, `requests.Session`) | 14,81 ms | 14,72 ms | 15,91 ms | 68 req/s |
| gRPC `GetEmployeeDataFromID(201)` | **1,57 ms** | 1,46 ms | 2,55 ms | **636 req/s** |
| REST `GET /employee` (todos, keep-alive) | 14,64 ms | 14,55 ms | 15,72 ms | 68 req/s |
| gRPC `ListAllEmployees()` | **1,35 ms** | 1,28 ms | 2,00 ms | **742 req/s** |

### Latência na mesma máquina (cliente e servidores no Linux, `127.0.0.1`)

| Operação | Média | Mediana | p95 | Vazão |
|---|---|---|---|---|
| REST `GET /employee/201` (conexão nova) | 2,70 ms | 2,68 ms | 3,53 ms | 370 req/s |
| REST `GET /employee/201` (keep-alive) | 2,37 ms | 2,30 ms | 3,28 ms | 422 req/s |
| gRPC `GetEmployeeDataFromID(201)` | **0,95 ms** | 0,89 ms | 1,32 ms | **1057 req/s** |
| REST `GET /employee` (todos, keep-alive) | 2,65 ms | 2,58 ms | 3,85 ms | 378 req/s |
| gRPC `ListAllEmployees()` | **1,21 ms** | 1,13 ms | 1,82 ms | **827 req/s** |

### Tamanho da resposta

| Resposta | REST (corpo JSON + cabeçalhos HTTP) | gRPC (payload protobuf) |
|---|---|---|
| um funcionário | 100 B + 167 B = **267 B** | **37 B** (+5 B de framing) |
| lista com 2 funcionários | 186 B + 167 B = **353 B** | **74 B** (+5 B de framing) |

O JSON repete o nome de cada campo em toda mensagem (`"name":`, `"title":`...) e manda números como texto. O protobuf manda só o número do campo (1 byte) e os valores em binário. Os cabeçalhos HTTP/1.1 vão em texto e se repetem a cada requisição, enquanto o HTTP/2 do gRPC comprime os cabeçalhos (HPACK) e reaproveita a mesma conexão.

**Cuidado ao interpretar:**

- A diferença na mesma máquina (~2,2 a 2,5x) é a mais justa para comparar protocolos.
- Entre as duas máquinas, o REST ficou em ~15 ms mesmo com keep-alive. Isso parece um efeito do servidor de desenvolvimento Werkzeug somado à rede virtual Windows<->WSL (provavelmente a interação entre o algoritmo de Nagle e o ACK atrasado do TCP, já que o Werkzeug escreve cabeçalho e corpo separados). Não é custo intrínseco do REST. Com um servidor de produção (gunicorn, nginx) esse número cairia bastante.
- Os dados não são idênticos (o REST tem `salary` e nomes diferentes), mas a diferença é de poucos bytes.
- Mesmo assim, o resultado segue o esperado: o gRPC é mais rápido e manda mensagens 4 a 7 vezes menores.

### Comportamento em erros (id inexistente)

| Situação | REST | gRPC |
|---|---|---|
| consultar id 999 | `200 OK` com `{"emp": []}` (o erro não aparece no status) | `StatusCode.UNKNOWN: Exception calling application: list index out of range` |
| alterar salário do id 999 | `500 Internal Server Error` com página HTML | n/a (operação não existe no exemplo gRPC) |
| endpoint inexistente | `404 NOT FOUND` | n/a: o método nem existe no stub (erro na hora de escrever o código) |
| id com tipo errado (`-1`) | aceito como string pela URL | `ValueError` no cliente, antes de enviar |

Os dois exemplos têm o mesmo defeito (não tratam o id inexistente), mas cada tecnologia mostra o erro do seu jeito. O gRPC tem códigos de status padronizados e semânticos (o certo seria `context.abort(NOT_FOUND)`). No REST a convenção seria devolver `404`, mas nada obriga.

### Abertura

O REST pode ser chamado por qualquer ferramenta HTTP, sem código gerado:

```
$ curl http://172.28.208.130:5678/empdb/employee
{"emps":[{"id":"201","name":"Rusmão Terceiro","salary":"4000","title":"Sr Software Engineer"}, ...]}
```

O mesmo `curl` na porta do gRPC não recebe resposta HTTP/1.1 (`http_code=000`). Para chamar o gRPC é preciso o `.proto` e stubs gerados, ou ferramentas específicas como `grpcurl` e Postman com reflection habilitada.

---

## 4. Comparação por critério

| Critério | RESTful | gRPC |
|---|---|---|
| **Eficiência** | JSON em texto, cabeçalhos verbosos, HTTP/1.1 (uma requisição por vez por conexão). Mais bytes e mais CPU para serializar | protobuf binário, HTTP/2 com multiplexação e cabeçalhos comprimidos. Nos testes, cerca de 2,2 a 2,5x menos latência (mesma máquina) e respostas 4 a 7x menores. Também tem streaming nos dois sentidos |
| **Modularidade** | o serviço é organizado em recursos, e cada endpoint é independente. Fácil de dividir em serviços menores atrás de um gateway | o serviço é organizado em interfaces (`service`) e mensagens. Os `.proto` podem ser importados e reaproveitados entre serviços (`import "common.proto"`) |
| **Manutenibilidade** | sem contrato formal, uma mudança no JSON do servidor quebra clientes **em tempo de execução**, e a documentação (OpenAPI) precisa ser mantida à parte. Por outro lado, o código é simples e fácil de depurar (JSON legível) | o contrato `.proto` documenta e versiona a API. Mudar um tipo quebra **na compilação/geração**. Protobuf tolera evolução: campos novos são ignorados por clientes antigos, desde que os números dos campos não sejam reaproveitados. Custo: um passo de geração de código no build |
| **Abertura (interoperabilidade)** | máxima: qualquer linguagem e qualquer cliente HTTP (navegador, `curl`, planilha, IoT) consomem a API. Formatos e padrões abertos e universais (HTTP, JSON, URL) | alta entre linguagens suportadas (o `protoc` gera código para C++, Java, Go, Python, C#...), mas exige o runtime gRPC e o `.proto`. Navegadores não falam gRPC nativo (precisa de gRPC-Web + proxy) |
| **Transparência de distribuição** | baixa: o cliente vê explicitamente que está fazendo requisições HTTP (URL, verbo, status, `response.json()`). Isso é honesto sobre a rede, mas dá mais trabalho | alta transparência de acesso: a chamada remota tem cara de chamada local (`stub.Metodo(msg)`) e o marshaling fica escondido. A localização continua explícita (`ip:porta` do canal), e falhas de rede ainda aparecem como exceções |
| **Acoplamento** | fraco: cliente e servidor só combinam URLs e formato. É o estilo arquitetural da Web (stateless, cacheável) | mais forte: cliente e servidor compartilham o mesmo contrato compilado |
| **Cache e infraestrutura** | aproveita caches HTTP (`GET` cacheável), CDNs, proxies, balanceadores e ferramentas de monitoramento existentes | o cache HTTP não se aplica (tudo é `POST` em HTTP/2). Balanceadores precisam entender HTTP/2 (o balanceamento é por requisição, não por conexão) |
| **Facilidade de depuração** | alta: dá para ler e reproduzir as mensagens com navegador ou `curl` | menor: as mensagens são binárias, e é preciso ferramenta própria para inspecionar |

---

## 5. Comparação mais ampla: frontend x backend

### APIs para aplicações de usuário final (frontend)

Navegadores, apps mobile, integrações de terceiros e APIs públicas.

**REST costuma ser a melhor escolha:**

- O **navegador fala HTTP/JSON nativamente** (`fetch`), sem bibliotecas nem proxy. O gRPC no navegador exige **gRPC-Web** e um proxy (Envoy) para traduzir, e não suporta todos os tipos de streaming.
- **Consumidores desconhecidos:** uma API pública é usada por pessoas e linguagens que o autor não controla. Uma URL documentada e um JSON legível têm a menor barreira de entrada.
- **Cache HTTP e CDN** reduzem a carga para dados lidos com frequência.
- A **depuração** pelo DevTools do navegador é direta.
- O ganho de eficiência do gRPC importa menos aqui, porque a latência da internet e da renderização domina o tempo. Em mobile, o payload menor do protobuf pode valer a pena (rede lenta, bateria), e alguns apps usam gRPC por isso.

Alternativas comuns no frontend são o GraphQL, quando o cliente precisa escolher exatamente os campos, e o WebSocket ou SSE para tempo real.

### APIs para interação entre serviços (backend)

Microsserviços dentro de um data center, sob controle da mesma organização.

**gRPC costuma ser a melhor escolha:**

- **Volume alto de chamadas internas:** uma requisição de usuário pode gerar dezenas de chamadas entre serviços. A latência e a CPU de serialização se somam, e a eficiência do protobuf/HTTP/2 faz diferença real (custo de infraestrutura e latência de cauda).
- **Contrato forte entre equipes:** o `.proto` é o acordo entre quem fornece e quem consome o serviço. Quebras aparecem no build, não em produção.
- **Poliglotismo:** serviços em Go, Java e Python compartilham o mesmo `.proto` com código gerado consistente.
- **Streaming** (cliente, servidor e bidirecional) nativo, útil para telemetria, filas e eventos.
- **Deadlines, cancelamento e códigos de status** padronizados se propagam entre serviços.
- Todos os clientes são conhecidos, então a necessidade de "abertura universal" é menor.

Um padrão muito usado combina as duas: **REST/JSON na borda** (um API Gateway voltado para o público) e **gRPC internamente**. Ferramentas como o *gRPC-Gateway* e o *transcoding* do Envoy geram a API REST a partir do próprio `.proto`.

### Fatores a considerar na escolha

1. **Quem são os clientes?** Navegador ou terceiros desconhecidos favorecem REST. Serviços internos e conhecidos favorecem gRPC.
2. **Requisitos de desempenho:** volume de chamadas, latência de cauda, tamanho das mensagens e banda (mobile, IoT) favorecem gRPC.
3. **Padrão de comunicação:** requisição e resposta simples funciona bem nos dois. Streaming contínuo ou bidirecional favorece gRPC.
4. **Contrato e evolução da API:** contrato forte e tipado com checagem em build favorece gRPC. Contrato flexível e fácil de explorar favorece REST (com OpenAPI para documentar).
5. **Infraestrutura existente:** proxies, caches, CDNs, WAFs e ferramentas de observabilidade baseados em HTTP/1.1 favorecem REST. Para gRPC, a infraestrutura precisa suportar HTTP/2 de ponta a ponta.
6. **Cache:** dados muito lidos e cacheáveis favorecem REST (`GET` + cabeçalhos de cache).
7. **Experiência da equipe e ecossistema:** REST é conhecido por praticamente todo desenvolvedor. O gRPC exige aprender protobuf, geração de código e novas ferramentas de depuração.
8. **Facilidade de depuração e testes manuais:** JSON legível e `curl` contra mensagens binárias e ferramentas específicas.
9. **Acoplamento aceitável:** REST mantém cliente e servidor mais independentes. O gRPC os prende ao mesmo contrato, o que é bom dentro de um sistema e ruim entre organizações.

**Resumo:** REST privilegia **abertura, simplicidade e baixo acoplamento**, ideal para a borda do sistema e APIs públicas. gRPC privilegia **eficiência, contrato forte e transparência de acesso**, ideal para a comunicação interna entre serviços. Não é uma escolha exclusiva, e muitos sistemas usam as duas, cada uma onde se encaixa melhor.
