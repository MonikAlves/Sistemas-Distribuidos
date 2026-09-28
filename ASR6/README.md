# ASR6: Novos métodos no exemplo ICE

**Disciplina:** Sistemas Distribuídos  
**Base:** [professorfabio/ice-demo](https://github.com/professorfabio/ice-demo) (Exemplo 3.21 do livro do Maarten van Steen)  
**Referência:** [ICE Middleware - Getting Started](https://docs.zeroc.com/ice/3.8/cpp/get-started)

---

## 1. O que foi implementado

O exemplo original tinha só um método na interface `Printer` (`printString`). Acrescentei três métodos novos na definição Slice ([Printer.ice](Printer.ice)):

```slice
module Demo
{
    sequence<string> StringSeq;

    interface Printer
    {
        string printString(string s);

        // Novos metodos
        string toUpper(string s);
        int countWords(string s);
        StringSeq getHistory();
    }
}
```

| Método | O que faz | Retorno |
|---|---|---|
| `toUpper(s)` | converte o texto para maiúsculas | `string` |
| `countWords(s)` | conta as palavras do texto | `int` |
| `getHistory()` | devolve todos os textos já impressos com `printString` naquele objeto | `StringSeq` (lista de strings) |

- Os métodos usam tipos diferentes do Slice: `string`, `int` e uma `sequence`, que no Python vira uma `list`.
- O `getHistory` mostra que cada servant guarda o próprio estado: no `server2.py`, `SimplePrinter1` e `SimplePrinter2` têm históricos separados.
- `server.py` e `server2.py` implementam os três métodos na classe `PrinterI`.
- `client.py` e `client2.py` chamam os métodos novos e imprimem os resultados.
- `Printer_ice.py` foi gerado de novo com `slice2py Printer.ice` (Ice 3.7).

---

## 2. Como executar

Antes, instale o middleware (seção 4) nas duas máquinas. Se alterar o `Printer.ice`, gere os stubs de novo:

```bash
slice2py Printer.ice
```

Servidor (na máquina com o IP configurado nos clientes):

```bash
python3 server2.py
```

Cliente:

```bash
python3 client2.py
```

Para testar tudo na mesma máquina, troque o IP `34.203.80.210` por `127.0.0.1` nos clientes.

---

## 3. Saída do teste (local)

Cliente (`client2.py`):

```
Hello World from printer1!*
Hello World from printer2!*
HELLO WORLD FROM PRINTER1!
4
printer1 history: ['Hello World from printer1!']
printer2 history: ['Hello World from printer2!']
```

Servidor (`server2.py`):

```
Object1 says: Hello World from printer1!
Object2 says: Hello World from printer2!
Object1 says: toUpper: Hello World from printer1!
Object2 says: countWords: Hello World from printer2!
```

---

## 4. Instalação do ICE (do README original)

Before running, install the middleware and associated tools (on both machines):

### On Amazon Linux
```
sudo dnf install https://download.zeroc.com/ice/3.7/amzn2023/ice-repo-3.7.amzn2023.noarch.rpm
```

```
sudo dnf install python3-ice ice-compilers
```

### On Ubuntu
```
wget "https://download.zeroc.com/ice/3.8/ubuntu26.04/ice-repo-3.8_1.0.0_all.deb" -O ice-repo.deb
sudo dpkg -i ice-repo.deb
rm ice-repo.deb
sudo apt-get update
```
```
sudo apt-get install python3-zeroc-ice
```
```
sudo apt-get install zeroc-ice-compilers
```
