# Validação dos quatro casos de normalização

Esta seção apresenta exatamente os quatro comportamentos exigidos para o
quarto estágio. A figura abaixo é gerada automaticamente a partir do VCD do
GHDL, não de valores digitados manualmente.

![Quatro casos obrigatórios de normalização](images/four-normalization-cases.svg)

Para reproduzir a figura e as formas de onda:

```bash
make normalization
python3 scripts/vcd_to_wave_svg.py \
    build/waves/normalization.vcd \
    docs/images/four-normalization-cases.svg
gtkwave build/waves/normalization.vcd
```

Arquivos produzidos:

```text
build/waves/normalization.vcd
build/waves/normalization.ghw
docs/images/four-normalization-cases.svg
```

## Validação visual da interface da placa

Além da forma de onda, o VCD do testbench de `top_fp_adder` é convertido em dois
painéis: o primeiro reproduz os seis estados de entrada, switches e LEDs; o
segundo mostra cinco resultados em `SHOW_RESULT`, incluindo underflow e
overflow com `LEDR8` apagado e cancelamento exato com `LEDR8` aceso.

```bash
make board-svg
```

![Entradas validadas no testbench da DE10-Lite](images/board-input-sequence.svg)

![Resultados validados no testbench da DE10-Lite](images/board-result-cases.svg)

O gerador decodifica os vetores físicos ativos em zero de `HEX5..HEX0`. Antes
de escrever o SVG, ele compara displays, `LEDR9..LEDR0`, operandos e resultado
de 13 bits com os valores esperados. Assim, a figura não é uma ilustração
manual: ela é uma apresentação mais legível dos dados presentes no VCD.

## Sinais observados

| Sinal VHDL | Função no algoritmo |
|---|---|
| `sum(8 downto 0)` | resultado da adição/subtração; `sum(8)` é carry |
| `leado(2 downto 0)` | quantidade de zeros à esquerda em `sum(7 downto 0)` |
| `sum_norm(7 downto 0)` | fração depois do deslocamento à esquerda |
| `expn(3 downto 0)` | expoente normalizado |
| `fracn(7 downto 0)` | fração normalizada |
| `sign_out` | sinal do operando de maior magnitude |

## Caso 1 — ordenar, alinhar e subtrair

```text
+0.10001010 × 2^3 + (−0.11011110 × 2^4)
```

O segundo operando é maior. A primeira fração é alinhada:

```text
10001010 >> 1 = 01000101
11011110 − 01000101 = 10011001
```

Como `sum(7)=1`, `leado=0`. Nenhum deslocamento adicional é necessário:

```text
resultado = 1 | 0100 | 10011001
          = −0.10011001 × 2^4
          = −9.5625
```

## Caso 2 — normalização à esquerda

```text
−0.10010000 × 2^3 + 0.10000000 × 2^3
```

```text
10010000 − 10000000 = 00010000
```

Existem três zeros antes do primeiro `1`:

```text
leado = 3
sum_norm = 00010000 << 3 = 10000000
expn = 3 − 3 = 0
```

Resultado:

```text
1 | 0000 | 10000000 = −0.5
```

Este caso comprova diretamente o contador e o deslocamento à esquerda.

## Caso 3 — underflow

```text
−0.10000001 × 2^0 + 0.10000000 × 2^0
```

```text
10000001 − 10000000 = 00000001
leado = 7
```

Normalizar exigiria `expn=0−7`, mas o expoente não possui valores negativos.
Como `leado > expb`, o Listing zera expoente e fração:

```text
1 | 0000 | 00000000
```

O sinal permanece `1` porque `sign_out=signb`; esse é o zero negativo do
código literal.

## Caso 4 — carry e normalização à direita

```text
+0.10010000 × 2^3 + 0.10000000 × 2^3
```

```text
010010000 + 010000000 = 100010000
```

`sum(8)=1`, portanto a prioridade é do ramo de carry:

```text
fracn = sum(8 downto 1) = 10001000
expn = 3 + 1 = 4
```

Resultado:

```text
0 | 0100 | 10001000 = +8.5
```

Neste caso, o valor de `leado` não controla a saída porque o teste de carry vem
antes do teste de zeros à esquerda.

## Conclusão sobre o quarto estágio

O deslocamento e a contagem funcionam corretamente nos quatro exemplos
obrigatórios. A análise adicional encontrou duas limitações do Listing 3.19:

- `leado=7` representa tanto `sum=1` quanto `sum=0`; cancelamento exato com
  expoente alto pode deixar expoente não zero e fração zero;
- carry com expoente 15 executa a soma de quatro bits `15+1=0`, pois não há
  sinalização de overflow.

Essas limitações são evidência de análise crítica e foram preservadas no modelo
original. Elas não invalidam os quatro exemplos exigidos.

## Captura no GTKWave

1. Execute `make normalization` e depois
   `gtkwave build/waves/normalization.vcd`.
2. Expanda `normalization_testbench/uut`.
3. Adicione `sum`, `leado`, `sum_norm`, `expn` e `fracn`.
4. Ajuste `case_index` para decimal.
5. Use os intervalos: caso 1 `0–20 ns`, caso 2 `20–40 ns`, caso 3 `40–60 ns`,
   caso 4 `60–80 ns`.
6. Capture a janela inteira com nomes, valores e escala de tempo legíveis.
