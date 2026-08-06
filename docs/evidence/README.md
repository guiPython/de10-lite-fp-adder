# Evidências que devem acompanhar a entrega

Não são criadas imagens fictícias. Os arquivos abaixo precisam ser produzidos
pelo grupo nas ferramentas e na placa reais.

| Arquivo sugerido | Evidência | Status |
|---|---|---|
| `gtkwave-normalization.png` | quatro casos, sinais do quarto estágio e escala 0–80 ns | pendente |
| `quartus-compilation.png` | compilação sem erros | pendente |
| `quartus-pin-planner.png` | pinos da DE10-Lite | pendente |
| `quartus-resources.png` | utilização de elementos lógicos e registradores | pendente |
| `quartus-timing.png` | clock de 50 MHz/20 ns analisado | pendente |
| `programmer-100-percent.png` | `.sof` programado com sucesso | pendente |
| `board-case-1.jpg` | resultado `001499`, LEDR9 aceso | pendente |
| `board-case-2.jpg` | resultado `001080`, LEDR9 aceso | pendente |
| `board-case-3.jpg` | resultado `001000`, zero por underflow e LEDR8 apagado | pendente |
| `board-case-4.jpg` | resultado `000488`, LEDR9 apagado | pendente |
| `board-case-5-overflow.jpg` | resultado `0000FF`, LEDR8 apagado | pendente |

Já é gerada automaticamente pelo repositório:

```text
docs/images/four-normalization-cases.svg
docs/images/board-input-sequence.svg
docs/images/board-result-cases.svg
```

## Como escrever uma legenda útil

Uma legenda deve identificar entrada, ramo exercitado e interpretação. Exemplo:

> Caso 2 — `sum=000010000`, `leado=3` e `sum_norm=10000000`. O expoente muda
> de 3 para 0, comprovando a normalização à esquerda. A saída
> `1|0000|10000000` representa −0.5.

Evite legendas como “simulação funcionando” ou “resultado da placa”, pois não
demonstram compreensão.

## Conferência antes do commit

- nomes dos sinais legíveis;
- escala de tempo visível;
- sem janelas cobrindo a forma de onda;
- foto da placa com switches, LEDs e displays no mesmo enquadramento;
- nenhuma imagem contém dados pessoais, chaves ou caminhos sensíveis;
- cada imagem é citada e interpretada no tutorial.
