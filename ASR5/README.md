# ASR5: Cliente-Servidor Multithread

**Disciplina:** Sistemas Distribuídos  
**Base:** código da [ASR4](../ASR4): cliente-servidor TCP com operações em JSON

---

## 1. O que foi implementado

1. **Servidor multithread** (`server.py --modo multi`)
   - Para cada conexão aceita, o servidor dispara uma `threading.Thread` nova que lê a requisição, processa e devolve a resposta. Como o cliente abre uma conexão por requisição, isso equivale a **uma thread por requisição**.
   - O modo `--modo single` mantém o comportamento da ASR4: a thread principal atende uma requisição de cada vez. Ele serve de base de comparação.
   - A lógica de processamento (`executar_operacao` / `processar_requisicao`) é a mesma da ASR4.

2. **Cliente multithread** (`client.py --modo multi`)
   - Cada requisição é enviada por uma thread nova, então várias requisições ficam em andamento ao mesmo tempo.
   - Um semáforo (`--concorrencia`, padrão 50) limita quantas threads existem simultaneamente, para não criar milhares de uma só vez.
   - Aceita **vários servidores** (`--servidores host:porta,host:porta`) e distribui as requisições entre eles em round-robin.
   - O modo `--modo single` envia uma requisição, espera a resposta e só então envia a próxima, como na ASR4.

3. **Geração automática de requisições**
   - `gerar_requisicao()` usa um gerador de números aleatórios (`random.Random(seed)`) para sortear a operação e os argumentos.
   - 70% das requisições têm uma operação avulsa e 30% são lotes de 2 a 5 operações.
   - Divisores zero e raízes de números negativos aparecem de propósito, para exercitar o tratamento de erro.
   - Com a mesma semente, todas as configurações recebem exatamente as mesmas requisições.

4. **Experimento automatizado** (`experimento.py`)
   - Sobe os servidores como processos separados, roda cada configuração 3 vezes e imprime a tabela de resultados em Markdown.

---

## 2. Como executar

```bash
# Servidor (multi é o padrão; use --modo single para a versão da ASR4)
python server.py --modo multi

# Cliente: 1000 requisições aleatórias, uma thread por requisição
python client.py --modo multi -n 1000

# Cliente sequencial (uma requisição por vez)
python client.py --modo single -n 1000

# Vários servidores
python server.py --porta 5678
python server.py --porta 5679
python client.py --servidores 127.0.0.1:5678,127.0.0.1:5679 -n 1000

# Mostrar algumas requisições geradas e as respostas
python client.py --exemplo

# Experimento completo (sobe e derruba os servidores sozinho)
python experimento.py -n 2000 --repeticoes 3 --atrasos 0,10
```

O `--atraso <ms>` do servidor simula um tempo de processamento por requisição, como um acesso a disco ou a banco de dados.

---

## 3. Relato do experimento

### Configuração

- Windows 11, 16 CPUs lógicas, Python 3.10.11. Cliente e servidores na mesma máquina (127.0.0.1).
- **2000 requisições** por execução, **3 repetições** por configuração (média ± desvio padrão), mesma semente aleatória.
- Cliente multi com até 50 threads simultâneas.
- Dois cenários de servidor:
  - **0 ms**: as operações originais, que levam microssegundos para executar.
  - **10 ms** de atraso simulado por requisição, para representar um serviço com processamento de verdade. No Windows o `sleep(0.01)` dura cerca de 15,6 ms por causa da resolução do relógio do sistema.

Configurações comparadas:

| | Cliente | Servidor | Observação |
|---|---|---|---|
| **A** | single | single | par single-threaded da ASR4 |
| **B** | single | multi | versão original, com multithreading só no servidor |
| **C** | multi | multi | versão nova da ASR5 |
| D | multi | single | extra: mostra o gargalo no servidor |
| E | multi | 2 × multi | extra: cliente enviando para dois servidores |

### Resultados

**Cenário 1: sem atraso (0 ms)**

| Configuração | Tempo total (s) | Vazão (req/s) | Speedup vs A |
|---|---|---|---|
| A. Cliente single + servidor single (ASR4) | 1.091 ± 0.184 | 1833 | 1.00x |
| B. Cliente single + servidor multi | 1.907 ± 0.258 | 1049 | 0.57x |
| C. Cliente multi + servidor multi | 0.954 ± 0.087 | 2096 | 1.14x |
| D. Cliente multi + servidor single | 0.822 ± 0.022 | 2433 | 1.33x |
| E. Cliente multi + 2 servidores multi | 0.747 ± 0.032 | 2678 | 1.46x |

**Cenário 2: 10 ms de processamento por requisição**

| Configuração | Tempo total (s) | Vazão (req/s) | Speedup vs A |
|---|---|---|---|
| A. Cliente single + servidor single (ASR4) | 32.255 ± 0.365 | 62 | 1.00x |
| B. Cliente single + servidor multi | 33.122 ± 0.127 | 60 | 0.97x |
| C. Cliente multi + servidor multi | 1.305 ± 0.093 | 1532 | **24.7x** |
| D. Cliente multi + servidor single | 31.973 ± 0.273 | 63 | 1.01x |
| E. Cliente multi + 2 servidores multi | 1.132 ± 0.017 | 1767 | **28.5x** |

A tabela completa, com latência média e p95, está em [resultados.md](resultados.md). Nenhuma configuração teve falhas.

### Análise

- **Multithreading só no servidor (B) não ajuda nada** quando o cliente é sequencial. Nunca há mais de uma requisição chegando ao mesmo tempo, então o servidor não tem o que paralelizar. Sem atraso, B fica até **mais lento** que A (0,57x), porque paga o custo de criar uma thread por requisição sem ganhar nada em troca.
- **O ganho só aparece com cliente e servidor multithread juntos (C).** Com 10 ms de processamento, as 2000 requisições caíram de 32,3 s para 1,3 s, cerca de **25 vezes mais rápido**. Enquanto uma thread do servidor espera, as outras continuam atendendo.
- **O servidor single-threaded é o gargalo (D).** Mesmo com 50 requisições em paralelo no cliente, D leva o mesmo tempo que A no cenário de 10 ms. As requisições só ficam na fila do `listen()`: a latência média sobe para ~790 ms, contra ~16 ms em A.
- **Dois servidores (E)** deram o melhor resultado nos dois cenários (28,5x com atraso), porque a carga é dividida entre dois processos independentes.
- **Sem atraso, as diferenças são pequenas** (entre 0,6x e 1,5x). Cada operação leva microssegundos e o tempo é dominado pelo custo de abrir a conexão TCP. Além disso, o GIL do Python impede que threads executem código Python em paralelo. As threads ajudam quando o trabalho **espera** (rede, disco, banco de dados), não quando é cálculo puro.
- **O limite teórico de C não foi atingido.** Com 50 threads e ~16 ms por requisição, o teto seria de ~3100 req/s, e C chegou a ~1530 req/s. A diferença vem do custo de criar threads e abrir conexões, que também disputam o GIL.

### Observação técnica

Na primeira rodada apareceram milhares de falhas de conexão. Cada requisição abre uma conexão TCP nova e, ao fechar, a conexão fica ~2 minutos em `TIME_WAIT`. Com dezenas de milhares de requisições, as ~16 mil portas efêmeras do Windows se esgotaram.

- Fazer o servidor fechar a conexão primeiro não resolveu. Como cliente e servidor estão na mesma máquina, o `TIME_WAIT` do lado do servidor também prende as portas.
- A correção foi fechar o socket do cliente com `SO_LINGER = 0`, só depois de a resposta completa ter chegado. Isso descarta a conexão na hora (RST) sem deixar `TIME_WAIT`. Depois disso, todas as execuções tiveram 0 falhas.
- Consequência: o servidor original da ASR4 não trata o RST (`ConnectionResetError`) e cai. Por isso a configuração A usa o `server.py --modo single` da ASR5, que tem a mesma lógica da ASR4 e só acrescenta esse tratamento.

---

## 4. Estrutura de arquivos

- `server.py`: servidor TCP com `--modo single` (ASR4) ou `--modo multi` (uma thread por requisição).
- `client.py`: cliente com gerador aleatório de requisições, `--modo single` ou `--modo multi` (uma thread por requisição).
- `experimento.py`: roda todas as configurações e imprime a tabela de resultados.
- `constCS.py`, `.env.example`, `.gitignore`: iguais aos da ASR4.
