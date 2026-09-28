# Resultados do experimento

- Máquina: Windows-10-10.0.26200-SP0, 16 CPUs lógicas, Python 3.10.11
- Cliente e servidores na mesma máquina (127.0.0.1)
- 2000 requisições por execução, 3 repetições por configuração (mesma semente aleatória em todas), até 50 threads simultâneas no cliente multi

## Atraso simulado no servidor: 0 ms por requisição

| Configuração | Tempo total (s) | Vazão (req/s) | Latência média (ms) | Latência p95 (ms) | Speedup vs A | Falhas |
|---|---|---|---|---|---|---|
| A. Cliente single + servidor single (ASR4) | 1.478 ± 0.402 | 1353.5 | 0.73 | 1.06 | 1.00x | 0 |
| B. Cliente single + servidor multi | 2.043 ± 0.355 | 978.9 | 1.02 | 1.49 | 0.72x | 0 |
| C. Cliente multi + servidor multi | 2.722 ± 2.315 | 734.7 | 65.77 | 98.62 | 0.54x | 1717 |
| D. Cliente multi + servidor single | 6.004 ± 0.428 | 333.1 | 145.91 | 188.72 | 0.25x | 5950 |
| E. Cliente multi + 2 servidores multi | 5.717 ± 0.039 | 349.8 | 138.27 | 185.99 | 0.26x | 5891 |

## Atraso simulado no servidor: 10 ms por requisição

| Configuração | Tempo total (s) | Vazão (req/s) | Latência média (ms) | Latência p95 (ms) | Speedup vs A | Falhas |
|---|---|---|---|---|---|---|
| A. Cliente single + servidor single (ASR4) | 7.363 ± 0.083 | 271.6 | 3.68 | 4.78 | 1.00x | 5996 |
| B. Cliente single + servidor multi | 6.987 ± 0.195 | 286.2 | 3.49 | 4.74 | 1.05x | 5992 |
| C. Cliente multi + servidor multi | 5.605 ± 0.223 | 356.9 | 135.77 | 176.87 | 1.31x | 5951 |
| D. Cliente multi + servidor single | 32.778 ± 0.220 | 61.0 | 808.51 | 868.62 | 0.22x | 0 |
| E. Cliente multi + 2 servidores multi | 1.349 ± 0.244 | 1482.9 | 27.21 | 43.35 | 5.46x | 0 |
