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
make converter-test
```

`DISPLAY` deve ter exatamente `00SEFF`. Informe `LEDR8`: `1` torna o valor
válido; `0` indica que os displays são apenas diagnóstico de underflow ou
overflow. Sem o LED, a validade fica desconhecida.
