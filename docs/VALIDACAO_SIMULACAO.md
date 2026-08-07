# Validação da normalização

O testbench possui `assert` para os quatro casos exigidos. A figura é gerada
do VCD, não preenchida manualmente.

```bash
make normalization
gtkwave build/waves/normalization.vcd
```

![Quatro casos obrigatórios](images/four-normalization-cases.svg)

## Sinais do quarto estágio

| Sinal | Função |
|---|---|
| `sum(8..0)` | soma/subtração; bit 8 é carry |
| `leado(2..0)` | zeros antes do primeiro `1` em `sum(7..0)` |
| `sum_norm(7..0)` | fração após shift à esquerda |
| `expn(3..0)` | expoente normalizado |
| `fracn(7..0)` | fração normalizada |

## Casos

### 1 — ordenar, alinhar e subtrair

```text
+0.10001010×2^3 + (−0.11011110×2^4)
10001010 >> 1 = 01000101
11011110 − 01000101 = 10011001
```

`leado=0`; saída `1|0100|10011001 = −9.5625`.

### 2 — normalizar à esquerda

```text
−0.10010000×2^3 + 0.10000000×2^3
10010000 − 10000000 = 00010000
leado=3
sum_norm=10000000
expn=3−3=0
```

Saída `1|0000|10000000 = −0.5`. Este caso comprova a contagem de três
zeros e o deslocamento correspondente.

### 3 — underflow

```text
−0.10000001×2^0 + 0.10000000×2^0
10000001 − 10000000 = 00000001
leado=7 > expb=0
```

Normalizar exigiria expoente `−7`; o Listing zera a magnitude. Saída
`1|0000|00000000`, com `underflow=1` na versão vetorial.

### 4 — carry e shift à direita

```text
0.10010000×2^3 + 0.10000000×2^3
010010000 + 010000000 = 100010000
fracn=sum(8..1)=10001000
expn=3+1=4
```

Saída `0|0100|10001000 = 8.5`.

## Conclusão

Os quatro ramos passaram. Foram também documentadas duas limitações do código
literal do livro:

- `leado=7` representa tanto `sum=1` quanto `sum=0`; um cancelamento exato
  com expoente alto pode manter expoente não zero;
- carry em expoente 15 faz o expoente de quatro bits retornar a zero.

O modelo original preserva esses comportamentos. `adder_unsigned` mantém o
mesmo `res` e acrescenta flags para a interface da placa.

## Interface da placa

```bash
make board-svg
```

![Estados de entrada](images/board-input-sequence.svg)

![Resultados da placa](images/board-result-cases.svg)

O gerador reconstrói displays e LEDs do VCD e falha se algum valor divergir
do esperado.

## Captura para o relatório

No GTKWave, expanda `normalization_testbench/uut`, adicione `sum`, `leado`,
`sum_norm`, `expn`, `fracn` e `case_index`, e mostre toda a janela de `0–80
ns`. A legenda deve explicar os quatro intervalos de 20 ns.
