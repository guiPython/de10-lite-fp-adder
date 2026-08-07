# Conversão decimal ↔ formato de 13 bits

## Formato

```text
[ S (1 bit) | E (4 bits) | F (8 bits) ]
value = (-1)^S × (F/256) × 2^E
```

`S=0` é positivo e `S=1` é negativo. `E` varia de 0 a 15. Para uma entrada
não nula normalizada, `128 ≤ F ≤ 255`.

Faixa em módulo:

```text
mínimo normalizado = (128/256) × 2^0  = 0.5
máximo normalizado = (255/256) × 2^15 = 32640
```

## Decimal para os campos

Para `x≠0`:

1. `S=0` se `x>0`; `S=1` se `x<0`.
2. Use `m=|x|`.
3. Escolha `E` tal que `0.5 ≤ m/2^E < 1`.
4. Calcule `F=floor((m/2^E)×256)`.
5. Recalcule o decimal para medir o erro de truncamento.

Zero é `0|0000|00000000`.

### Exato: `13.25`

```text
13.25 / 2^4 = 0.11010100₂
S=0, E=4=0100₂, F=212=11010100₂
palavra: 0|0100|11010100
```

Conferência: `(212/256)×2^4=13.25`.

### Exato: `−9.5625`

```text
S=1, E=4, F=153=10011001₂=0x99
palavra: 1|0100|10011001
```

Conferência: `−(153/256)×2^4=−9.5625`. Na saída da placa: `001499`,
`LEDR9=1`, `LEDR8=1`.

### Truncado: `3.14`

```text
3.14 / 2^2 = 0.785
F=floor(0.785×256)=200
representado=(200/256)×2^2=3.125
erro=3.125−3.14=−0.015
```

O erro é esperado porque o modelo ignora arredondamento.

## Previsão do erro da soma

Para um campo com expoente `E`, a distância entre dois valores consecutivos é:

```text
resolução = Δ(E) = 2^(E−8)
```

O alinhamento usa o maior expoente e desloca a fração do menor operando para
a direita. Cada bit descartado representa informação perdida. Se a adição
gerar carry, a normalização desloca novamente a fração para a direita e dobra
a resolução.

O comando abaixo reproduz essas etapas exatamente como o VHDL:

```bash
make result A=5000 B=1000
```

Ele mostra as palavras de 13 bits, expoentes, diferença dos expoentes, frações
alinhadas, resolução, erros intermediários, saída `00SEFF` e comparação
decimal.

### Exemplo: `5000 + 1000`

```text
5000 -> 4992                 erro de codificação = -8
1000 -> 1000                 erro de codificação =  0
E comum = 13; Δ = 32
1000 alinhado -> 992         erro de alinhamento = -8
resultado obtido = 5984      erro total = -16
saída da placa = 000DBB
```

### Exemplo: `1.5 + 3.4`

```text
1.5 -> 1.5
3.4 -> 3.390625              erro de codificação = -0.009375
soma depois do alinhamento = 4.890625
carry: E muda de 2 para 3; Δ muda de 0.015625 para 0.03125
resultado obtido = 4.875     erro de normalização = -0.015625
erro total = -0.025
saída da placa = 00039C
```

O resultado matemático esperado e o obtido só coincidem quando todas as
informações necessárias cabem no formato durante codificação, alinhamento e
normalização.

## Campos para decimal

Leia `S`, converta `E` e `F` como inteiros sem sinal e aplique a fórmula.

Exemplo:

```text
1|0100|10011001
= −(153/256) × 2^4
= −9.5625
```

Nos displays, a mesma palavra aparece como:

```text
00 | 1 | 4 | 99 = 001499
     S   E   FF
```

Os dois zeros são apenas extensão para usar os seis displays.

## Referência rápida

| Decimal | `S` | `E` | `F` | Palavra |
|---:|---:|---:|---:|---|
| `0.5` | 0 | 0 | 128 | `0|0000|10000000` |
| `1` | 0 | 1 | 128 | `0|0001|10000000` |
| `10` | 0 | 4 | 160 | `0|0100|10100000` |
| `13.25` | 0 | 4 | 212 | `0|0100|11010100` |
| `−9.5625` | 1 | 4 | 153 | `1|0100|10011001` |
| `32640` | 0 | 15 | 255 | `0|1111|11111111` |

Magnitudes menores que `0.5` sofrem underflow; maiores que `32640`, como
`50000`, sofrem overflow.

## Conferência automática

```bash
make encode INPUT=13.25
make decode DISPLAY=001499 LEDR8=1
make result A=5000 B=1000
make converter-test
```

`DISPLAY` deve ter exatamente `00SEFF`. Informe `LEDR8`: `1` torna o valor
válido; `0` indica que os displays são apenas diagnóstico de underflow ou
overflow. Sem o LED, a validade fica desconhecida.
