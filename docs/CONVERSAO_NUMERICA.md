# Conversão decimal ↔ formato normalizado de 13 bits

Este guia demonstra o caminho completo exigido pela rubrica:

```text
decimal → forma normalizada → campos binários de 13 bits
campos binários de 13 bits → forma normalizada → decimal
```

## 1. Definição do formato

```text
bit 12       bits 11..8       bits 7..0
+-------+----------------+-------------------+
| sign  | exponent (e)   | fraction (f)      |
+-------+----------------+-------------------+
```

O valor é:

```text
value = (-1)^sign × 0.f × 2^e
      = (-1)^sign × (f/256) × 2^e
```

Para um número não nulo estar normalizado, `f(7)=1`. Logo, `f` deve estar
entre 128 e 255. O expoente é sem sinal e varia de 0 a 15.

## 2. Decimal para 13 bits

Para converter um número decimal `x`:

1. Separe o sinal: `sign=0` para positivo e `sign=1` para negativo.
2. Trabalhe com a magnitude `m=|x|`.
3. Escolha `e` de forma que `0.5 ≤ m/2^e < 1`.
4. Calcule `f_real=(m/2^e)×256`.
5. Como o livro ignora arredondamento, use `f=floor(f_real)`.
6. Escreva `sign` em 1 bit, `e` em 4 bits e `f` em 8 bits.
7. Recalcule o valor representado para conhecer o erro.

Para `m≥1`, uma forma direta de encontrar o expoente é:

```text
e = floor(log2(m)) + 1
```

Zero é tratado separadamente como `0 0000 00000000`.

### Exemplo A — conversão exata de +13.25

```text
sign = 0
13.25 / 2^4 = 0.828125 = 0.11010100₂
e = 4 = 0100₂
f = 11010100₂ = 212
```

Palavra empacotada:

```text
0 0100 11010100
```

Conferência:

```text
(212/256) × 2^4 = 13.25
```

Na placa, a entrada é `S=0`, `F=212`, `E=4`. Se esse valor aparecer como
resultado, os displays mostram `0004D4` e `LEDR9` fica apagado.

### Exemplo B — conversão exata de −9.5625

```text
sign = 1
9.5625 / 2^4 = 0.59765625 = 0.10011001₂
e = 4 = 0100₂
f = 10011001₂ = 153 = 0x99
```

Palavra empacotada:

```text
1 0100 10011001
```

Conferência:

```text
−(153/256) × 2^4 = −153/16 = −9.5625
```

Na saída da placa: `001499`, `LEDR9` aceso e `LEDR8` aceso.

### Exemplo C — valor que sofre truncamento: 3.14

```text
sign = 0
3.14 / 2^2 = 0.785
f_real = 0.785 × 256 = 200.96
f = floor(200.96) = 200 = 11001000₂
e = 2 = 0010₂
```

Palavra:

```text
0 0010 11001000
```

Valor efetivamente representado:

```text
(200/256) × 2^2 = 3.125
erro = 3.125 − 3.14 = −0.015
```

Esse erro é esperado: os bits descartados não são arredondados.

## 3. Treze bits para decimal

Para fazer o caminho inverso:

1. Leia o bit 12 como sinal.
2. Converta os bits 11..8 para o expoente sem sinal `e`.
3. Converta os bits 7..0 para o inteiro sem sinal `f`.
4. Calcule `(-1)^sign × (f/256) × 2^e`.

### Exemplo D — saída do primeiro caso do livro

```text
bits = 1 0100 10011001
sign = 1
e = 0100₂ = 4
f = 10011001₂ = 153
```

```text
value = −(153/256) × 2^4
      = −153/16
      = −9.5625
```

O display `001499` é a palavra de 13 bits estendida com zeros até 24 bits:

```text
00 | 1 | 4 | 99
     S   E   FF
```

Somente os quatro últimos dígitos contêm a palavra empacotada: sinal `1`,
expoente `4` e fração `0x99`. Os dois primeiros zeros não acrescentam dados.

## 4. Tabela de referência

| Decimal solicitado | `sign` | `e` | `f` decimal/binário | Palavra de 13 bits | Decimal representado |
|---:|---:|---:|---|---|---:|
| `0` | 0 | 0 | `0 / 00000000` | `0 0000 00000000` | `0` |
| `0.5` | 0 | 0 | `128 / 10000000` | `0 0000 10000000` | `0.5` |
| `0.75` | 0 | 0 | `192 / 11000000` | `0 0000 11000000` | `0.75` |
| `1` | 0 | 1 | `128 / 10000000` | `0 0001 10000000` | `1` |
| `10` | 0 | 4 | `160 / 10100000` | `0 0100 10100000` | `10` |
| `13.25` | 0 | 4 | `212 / 11010100` | `0 0100 11010100` | `13.25` |
| `−9.5625` | 1 | 4 | `153 / 10011001` | `1 0100 10011001` | `−9.5625` |
| `3.14` | 0 | 2 | `200 / 11001000` | `0 0010 11001000` | `3.125` |
| `32640` | 0 | 15 | `255 / 11111111` | `0 1111 11111111` | `32640` |

Valores entre zero e `0.5` sofrem underflow. Magnitudes maiores que `32640`,
como `50000`, não cabem no formato.

## 5. Conferência automatizada

O script não substitui a compreensão do cálculo; ele serve para conferir os
exercícios feitos manualmente:

```bash
make encode INPUT=13.25
make encode INPUT=-9.5625
make decode DISPLAY=001499 LEDR8=1
make converter-test
```

O alvo `decode` corresponde diretamente aos seis displays. Ele separa
`001499` em `sign=1`, `exponent=0x4` e `fraction=0x99`, calcula `−9.5625` e
informa que `LEDR9` deve estar aceso.

O formato aceito é exatamente `00SEFF`: os dois primeiros zeros são extensão,
`S` é o sinal, `E` é o expoente hexadecimal e `FF` é a fração hexadecimal.
Com `LEDR8=1`, o valor decodificado representa a soma. Com `LEDR8=0`, os campos
são exibidos apenas para diagnóstico porque ocorreu underflow ou overflow. Se
`LEDR8` for omitido, o script informa que a validade é desconhecida.

Antes de aceitar a conversão, confira `LEDR8`: aceso significa que o resultado
é representável; apagado na tela hexadecimal significa underflow ou overflow.
Nesse caso, a palavra continua visível para diagnóstico, mas não representa a
soma exata. Um zero obtido por cancelamento exato mantém `LEDR8` aceso.

O teste automatizado verifica conversões exatas, truncamento, zero, limites da
representação e valores fora da faixa.

## 6. Exercícios para apresentação oral

Antes da demonstração, cada integrante deve conseguir resolver sem o script:

1. Converter `10` para os campos e voltar para decimal.
2. Converter `−9.5625` para a palavra de 13 bits.
3. Explicar por que `3.14` vira `3.125`.
4. Explicar por que `50000` não pode ser inserido.
5. Ler `1 0100 10011001` e obter `−9.5625`.

Respostas: `10 → 0 0100 10100000`; `−9.5625 → 1 0100 10011001`;
`3.14` perde os bits além dos oito disponíveis; o limite superior é `32640`.
