# ASR8: RPC multiplataforma com ICE (Python <-> Java)

**Disciplina:** Sistemas Distribuídos  
**Base:** Tarefa anterior com ICE ([ASR6](../ASR6)) e Lista ASR 07  
**Referência:** [ICE Middleware - Getting Started](https://docs.zeroc.com/ice/3.8/cpp/get-started)

---

## 1. O que foi implementado

A mesma interface Slice ([Printer.ice](Printer.ice)) é implementada em duas linguagens. Assim qualquer cliente conversa com qualquer servidor:

| Cenário | Cliente | Servidor |
|---|---|---|
| 1 | Python ([python/client.py](python/client.py)) | Java ([java/src/Server.java](java/src/Server.java)) |
| 2 | Java ([java/src/Client.java](java/src/Client.java)) | Python ([python/server.py](python/server.py)) |

A interface é a da ASR6, com um método novo, `getPlatform()`. Ele devolve a linguagem, a versão do Ice e o sistema operacional do servidor, para o cliente ver de onde veio a resposta:

```slice
module Demo
{
    sequence<string> StringSeq;

    interface Printer
    {
        string printString(string s);
        string toUpper(string s);
        int countWords(string s);
        StringSeq getHistory();
        string getPlatform();
    }
}
```

Os stubs e skeletons foram gerados a partir do mesmo `.ice`:

```bash
slice2py   --output-dir python         Printer.ice   # gera python/Printer_ice.py e python/Demo/
slice2java --output-dir java/generated Printer.ice   # gera java/generated/Demo/*.java
```

Estrutura:

```
ASR8/
├── Printer.ice              # contrato único, independente de linguagem
├── python/
│   ├── server.py            # servant PrinterI em Python
│   ├── client.py            # cliente Python
│   ├── Printer_ice.py       # gerado pelo slice2py
│   └── Demo/__init__.py     # gerado pelo slice2py
└── java/
    ├── src/
    │   ├── PrinterI.java    # servant PrinterI em Java
    │   ├── Server.java
    │   └── Client.java
    └── generated/Demo/      # gerado pelo slice2java
```

---

## 2. Como executar

O servidor sempre escuta na porta `5678`. O cliente recebe o IP do servidor como argumento (padrão `127.0.0.1`).

### Python

```bash
cd python
python3 server.py                 # servidor
python3 client.py <IP_SERVIDOR>   # cliente
```

### Java

É preciso o jar do Ice para Java (`com.zeroc:ice:3.7.x`). No Ubuntu ele vem no pacote `libzeroc-ice-java` (`/usr/share/java/ice-3.7.6.jar`). Também dá para baixar do Maven Central:

```bash
curl -LO https://repo1.maven.org/maven2/com/zeroc/ice/3.7.10/ice-3.7.10.jar
```

Compilar e rodar (no Windows troque `:` por `;` no classpath):

```bash
cd java
javac -cp ice-3.7.10.jar -d build src/*.java generated/Demo/*.java
java  -cp build:ice-3.7.10.jar Server                  # servidor
java  -cp build:ice-3.7.10.jar Client <IP_SERVIDOR>    # cliente
```

### Instalação do ICE

- **Ubuntu 22.04:** `sudo apt-get install zeroc-ice-compilers python3-zeroc-ice libzeroc-ice-java`
- **Amazon Linux / Ubuntu (repositório da ZeroC):** ver a seção 4 do [README da ASR6](../ASR6/README.md)

---

## 3. Testes realizados

Testei em duas máquinas diferentes: o Windows 11 (host) e um Ubuntu 22.04 no WSL2, que é uma VM com IP próprio (`172.28.208.130`, enquanto o host é `172.28.208.1`). A comunicação passa pela rede virtual entre os dois.

### Cenário 1: cliente Python (Linux) -> servidor Java (Windows)

Servidor (Windows, Java 17 + Ice 3.7.10):

```
Servidor Java pronto na porta 5678
Hello World from Python!
toUpper: Hello World from Python!
countWords: Hello World from Python client
```

Cliente (Linux, Python 3.10 + Ice 3.7.6): `python3 client.py 172.28.208.1`

```
Cliente Python -> servidor: Java 17.0.10 / Ice 3.7.10 / Windows 11
Hello World from Python!*
HELLO WORLD FROM PYTHON!
5
['Hello World from Python!']
```

### Cenário 2: cliente Java (Windows) -> servidor Python (Linux)

Servidor (Linux, Python 3.10 + Ice 3.7.6):

```
Servidor Python pronto na porta 5678
Hello World from Java!
toUpper: Hello World from Java!
countWords: Hello World from Java client
```

Cliente (Windows, Java 17 + Ice 3.7.10): `java -cp "build;ice-3.7.10.jar" Client 172.28.208.130`

```
Cliente Java -> servidor: Python 3.10.12 / Ice 3.7.6 / Linux
Hello World from Java!*
HELLO WORLD FROM JAVA!
5
[Hello World from Java!]
```

Além de linguagem e sistema operacional diferentes, os dois lados usavam versões diferentes do Ice (3.7.10 e 3.7.6) e funcionaram sem nenhuma adaptação, porque o protocolo e a codificação de dados (encoding 1.1) são os mesmos.

---

## 4. Discussão: middleware x camada de transporte

**Com o middleware (ICE)**, o contrato fica em um único arquivo `.ice`, e o `slice2py`/`slice2java` gera os stubs e skeletons de cada linguagem. O cliente chama `printer.countWords("...")` como se fosse um método local e recebe um `int`. Em Python o `StringSeq` vira `list` e em Java vira `String[]`. Não escrevi nada sobre formato de mensagem, conversão de tipos, ordem de bytes ou conexão.

**Sem o middleware**, direto sobre TCP como nas ASR4/ASR5, eu teria que:

- **Definir um protocolo de aplicação** (formato da mensagem, delimitador, códigos de operação e de erro) e implementar esse protocolo duas vezes, uma em cada linguagem, mantendo as duas versões iguais.
- **Fazer o marshaling à mão.** O `pickle`, usado no exemplo `rpc1` do material da disciplina, só existe em Python e não serve para Java. Seria preciso um formato neutro (JSON, por exemplo) e cuidar de tipos: o `int` do Java tem 32 bits e o do Python não tem limite, strings precisam de codificação definida, listas e sequências precisam de conversão.
- **Tratar o enquadramento das mensagens no fluxo TCP** (um `recv(1024)` pode receber meia mensagem), timeouts, reconexão e erros de rede nos dois lados.
- **Escrever stubs e despachantes** que transformam a chamada em mensagem e a mensagem em chamada, para cada operação e em cada linguagem.

### Benefícios do middleware neste cenário

- **Transparência de acesso:** a chamada remota tem a mesma forma de uma chamada local, e as diferenças de linguagem, tipos e representação de dados ficam escondidas pelo marshaling padronizado (questão 5a da ASR07).
- **Interoperabilidade:** o contrato `.ice` é a única fonte de verdade. Um servidor Java atende um cliente Python sem que nenhum dos dois saiba disso, e outras linguagens (C++, C#, JS) poderiam entrar sem mudar o servidor.
- **Menos código e menos erros:** o código gerado garante que os dois lados concordam com a assinatura dos métodos. Uma mudança na interface é feita no `.ice` e propagada ao regerar os stubs.
- **Transparência de localização (parcial):** o endereço fica só na string do proxy (`SimplePrinter:tcp -h ... -p 5678`), que poderia vir de configuração ou de um serviço de localização (IceGrid).
- **Serviços prontos:** gerenciamento de conexões, exceções remotas tipadas, chamadas assíncronas, SSL e retry já vêm no ICE.

### Implicações e custos

- **Dependência do middleware:** todas as máquinas precisam do runtime do ICE na linguagem certa e do compilador Slice. Na prática foi a parte mais trabalhosa: o pacote `python3-zeroc-ice` do Ubuntu 22.04 veio sem o submódulo `Ice.Py3`, e no Windows o `pip install zeroc-ice` não tem wheel pronta para Python 3.10, então precisa compilar.
- **Acoplamento ao contrato e à ferramenta:** os dois lados precisam usar ICE (o protocolo é próprio, não dá para falar com um cliente HTTP comum) e versões compatíveis.
- **Overhead:** cabeçalhos do protocolo Ice, verificação de tipo (o `checkedCast` faz uma ida e volta extra) e camadas adicionais. Para mensagens muito simples, um socket "cru" pode ser mais leve.
- **A transparência pode enganar:** a chamada parece local, mas pode falhar ou demorar por causa da rede. O programador ainda precisa tratar exceções como `ConnectionRefusedException` e timeouts.

**Conclusão:** em um cenário multiplataforma e multilinguagem, o middleware compensa. Ele troca um custo inicial de instalação e dependência por um contrato único, código gerado e consistente nas duas linguagens e muito menos código de comunicação para manter. Construir sobre a camada de transporte só faz sentido quando é preciso controle total do protocolo ou o mínimo de overhead.
