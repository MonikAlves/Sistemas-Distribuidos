# Resultados do experimento

- Máquina: Windows-10-10.0.26200-SP0, 16 CPUs lógicas, Python 3.10.11
- Cliente e servidores na mesma máquina (127.0.0.1)
- 2000 requisições por execução, 3 repetições por configuração (mesma semente aleatória em todas), até 50 threads simultâneas no cliente multi

## Atraso simulado no servidor: 0 ms por requisição

| Configuração | Tempo total (s) | Vazão (req/s) | Latência média (ms) | Latência p95 (ms) | Speedup vs A | Falhas |
|---|---|---|---|---|---|---|
| A. Cliente single + servidor single (ASR4) | 1.005 ± 0.102 | 1990.0 | 0.50 | 0.69 | 1.00x | 0 |
| B. Cliente single + servidor multi | 1.337 ± 0.187 | 1495.4 | 0.67 | 0.88 | 0.75x | 0 |
| C. Cliente multi + servidor multi | 0.832 ± 0.039 | 2402.6 | 19.90 | 22.69 | 1.21x | 0 |
| D. Cliente multi + servidor single | 0.620 ± 0.050 | 3226.5 | 13.03 | 16.19 | 1.62x | 0 |
| E. Cliente multi + 2 servidores multi | 0.601 ± 0.044 | 3325.6 | 1.15 | 1.50 | 1.67x | 0 |

## Atraso simulado no servidor: 10 ms por requisição

| Configuração | Tempo total (s) | Vazão (req/s) | Latência média (ms) | Latência p95 (ms) | Speedup vs A | Falhas |
|---|---|---|---|---|---|---|
| A. Cliente single + servidor single (ASR4) | 31.923 ± 0.472 | 62.7 | 15.95 | 22.76 | 1.00x | 0 |
| B. Cliente single + servidor multi | 33.038 ± 0.100 | 60.5 | 16.51 | 24.25 | 0.97x | 0 |
| C. Cliente multi + servidor multi | 1.253 ± 0.021 | 1596.6 | 25.91 | 34.56 | 25.48x | 0 |
| D. Cliente multi + servidor single | 31.886 ± 0.152 | 62.7 | 786.18 | 838.70 | 1.00x | 0 |
| E. Cliente multi + 2 servidores multi | 1.059 ± 0.063 | 1888.9 | 20.51 | 28.23 | 30.15x | 0 |
