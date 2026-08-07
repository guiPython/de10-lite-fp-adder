# Evidências da entrega

Não use imagens fictícias. Produza estas capturas nas ferramentas e na placa:

| Arquivo sugerido | Deve mostrar |
|---|---|
| `gtkwave-normalization.png` | `sum`, `leado`, `sum_norm`, `expn`, `fracn` e `0–80 ns` |
| `quartus-compilation.png` | Full Compilation successful e dispositivo correto |
| `quartus-pin-planner.png` | portas e pinos da DE10-Lite |
| `quartus-resources.png` | utilização de lógica e registradores |
| `quartus-timing.png` | clock de 50 MHz/20 ns |
| `programmer-100-percent.png` | `.sof` programado com sucesso |
| `board-case-1.jpg` | `001499`, `LEDR9=1`, `LEDR8=1` |
| `board-case-2.jpg` | `001080`, `LEDR9=1`, `LEDR8=1` |
| `board-case-3.jpg` | `001000`, `LEDR9=1`, `LEDR8=0` |
| `board-case-4.jpg` | `000488`, `LEDR9=0`, `LEDR8=1` |
| `board-case-5-overflow.jpg` | `0000FF`, `LEDR8=0` |

Já gerados automaticamente do VCD:

- `docs/images/four-normalization-cases.svg`;
- `docs/images/board-input-sequence.svg`;
- `docs/images/board-result-cases.svg`.

Cada legenda deve informar entrada, ramo exercitado, saída binária e conversão
decimal. Antes do commit, confira legibilidade, escala de tempo e ausência de
dados pessoais ou caminhos sensíveis.
