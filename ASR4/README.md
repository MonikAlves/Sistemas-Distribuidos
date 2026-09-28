# Atividade Prática: Sistema Cliente-Servidor (Capítulo 2)

**Disciplina:** Sistemas Distribuídos  
**Base:** Slide 5 (Capítulo 2)  

---

## 1. O que foi implementado

A partir do exemplo base fornecido na aula (em que o servidor apenas recebia `"Hello World"` e devolvia `"Hello World*"`), fiz as seguintes alterações para atender aos requisitos pedidos:

1. **Processamento da requisição no servidor**:
   - O servidor agora processa os dados enviados pelo cliente e calcula o resultado real.
   - Foram implementadas operações matemáticas (`soma`, `subtracao`, `multiplicacao`, `divisao`, `potencia`, `raiz`, `porcentagem`), manipulação de strings (`maiuscula`, `minuscula`, `inverter`, `contar_palavras`) e utilitários (`hora`, `eco`).
   - Adicionei tratamento de erros (como divisão por zero e raiz de número negativo) para evitar que o servidor caia durante a execução.

2. **Chamar mais de uma funcionalidade por requisição**:
   - O cliente pode agrupar várias operações diferentes em uma mesma mensagem de requisição (`operations: [...]`).
   - O servidor recebe esse lote, executa cada uma das operações e devolve todos os resultados juntos em uma única resposta TCP.
   - O cliente também pode fazer chamadas avulsas normais (uma operação por requisição).

3. **Configuração com `.env` e `.env.example`**:
   - Para não deixar o IP fixo no código (`constCS.py`), criei os arquivos `.env` e `.env.example`.
   - O `constCS.py` lê as variáveis `CS_HOST` e `CS_PORT` do `.env` se ele existir, ou usa `127.0.0.1` e porta `5678` como padrão.

---

## 2. Como as mensagens funcionam (Protocolo)

A comunicação é feita via socket TCP utilizando JSON codificado em UTF-8, terminando sempre com uma quebra de linha (`\n`) para indicar o fim da mensagem.

### Exemplo 1: Requisição de uma única operação
```json
{
  "op": "soma",
  "args": [10, 25, 15]
}
```

### Exemplo 2: Requisição com mais de uma funcionalidade (Lote)
```json
{
  "operations": [
    {"op": "potencia", "args": [2, 8]},
    {"op": "raiz", "args": [144]},
    {"op": "multiplicacao", "args": [6, 7]},
    {"op": "maiuscula", "args": ["teste"]},
    {"op": "contar_palavras", "args": ["sistemas distribuidos ufg"]}
  ]
}
```

### Resposta do Servidor:
```json
{
  "status": "success",
  "total": 5,
  "results": [
    {"op": "potencia", "args": [2, 8], "status": "ok", "result": 256},
    {"op": "raiz", "args": [144], "status": "ok", "result": 12.0},
    {"op": "multiplicacao", "args": [6, 7], "status": "ok", "result": 42},
    {"op": "maiuscula", "args": ["teste"], "status": "ok", "result": "TESTE"},
    {"op": "contar_palavras", "args": ["sistemas distribuidos ufg"], "status": "ok", "result": 3}
  ]
}
```

Caso alguma operação tenha erro (exemplo: divisão por zero), ela retorna `status: "error"` com a mensagem de erro, enquanto as demais operações do lote são executadas normalmente.

---

## 3. Estrutura de Arquivos

- `server.py`: Código do servidor TCP com o processamento das funções.
- `client.py`: Código do cliente com menu interativo e modo de teste automático.
- `constCS.py`: Arquivo de constantes que carrega o `.env`.
- `.env`: Configurações de rede locais (ignorado no Git).
- `.env.example`: Arquivo de exemplo para configuração de IP e porta.
- `.gitignore`: Arquivos e pastas ignoradas pelo Git.

---

## 4. Como Executar

### 1. Iniciar o Servidor
Abra um terminal na pasta do projeto e rode:
```bash
python server.py
```

### 2. Executar o Cliente
Abra outro terminal e escolha como quer rodar:

- **Modo Demonstração (executa testes automáticos de todos os requisitos):**
  ```bash
  python client.py --demo
  ```

- **Modo Interativo (menu no terminal):**
  ```bash
  python client.py
  ```

- **Comando direto via terminal:**
  ```bash
  python client.py --op soma --args 10 20 30
  ```
