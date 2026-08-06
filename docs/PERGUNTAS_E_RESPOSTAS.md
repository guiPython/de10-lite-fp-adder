# Perguntas e respostas do projeto

## 1. O que o circuito deve fazer?

Receber dois números no formato simplificado de 13 bits, somá-los segundo o
algoritmo do livro e devolver outro número no mesmo formato:

```text
[ sign (1 bit) | exponent (4 bits) | fraction (8 bits) ]
```

## 2. Entram dois números de 13 bits e sai um número de 13 bits?

Sim. A interface empacotada é:

```vhdl
a, b : in  unsigned(12 downto 0);
res  : out unsigned(12 downto 0);
```

Isso representa 26 bits de entrada e 13 bits de saída. Bits temporários
internos não alteram a largura da interface.

## 3. Por que o livro usa uma soma interna de 9 bits?

As frações têm 8 bits. Ao somar duas frações alinhadas pode surgir carry, por
isso o livro usa:

```vhdl
signal sum : unsigned(8 downto 0);
```

O nono bit é apenas o carry. Depois da normalização, o resultado volta aos oito
bits de fração e quatro bits de expoente, além do sinal.

## 4. Por que não usamos mais os 25 bits internos?

Os 25 bits pertenciam a uma interpretação alternativa, `k × 2^e`, que
preservava a soma inteira exata antes de quantizar. Ela não reproduzia o
algoritmo do livro, que alinha uma fração de 8 bits e descarta os bits que saem
durante o deslocamento. Para fidelidade à atividade, essa implementação deixou
de ser o núcleo principal.

## 5. Qual é o valor matemático correto dos campos?

Segundo o livro:

```text
(-1)^sign × 0.fraction × 2^exponent
```

Como `0.fraction = fraction/256`, o campo `fraction` não é um inteiro isolado.
Por exemplo:

```text
sign=0, fraction=195, exponent=8
= +(195/256) × 256
= 195
```

## 6. Como o sinal é representado?

É uma representação por sinal e módulo, não complemento de dois:

| Sinal | Significado |
|---:|---|
| `0` | positivo |
| `1` | negativo |

Internamente, a soma do livro continua sendo feita com magnitudes e uma
decisão entre adição e subtração.

## 7. Quais números são entradas válidas?

O livro exige representação normalizada ou zero. Para uma entrada não nula, o
MSB da fração deve ser `1`, portanto `fraction` deve estar entre 128 e 255.

```text
menor magnitude = 0.10000000₂ × 2^0 = 0.5
maior magnitude = 0.11111111₂ × 2^15 = 32640
```

Entradas não normalizadas podem produzir algum resultado lógico no circuito,
mas estão fora das hipóteses matemáticas do livro.

## 8. O número 50000 pode ser representado?

Não no formato estrito do livro. O maior módulo é 32640. A codificação
`fraction=195, exponent=8` representa 195, e não 49920.

A interpretação anterior `195 × 2^8 = 49920` foi uma decisão provisória
baseada em outro formato e foi substituída após a conferência do capítulo.

## 9. Quais são os quatro estágios do algoritmo?

1. **Sorting:** seleciona os operandos de maior e menor magnitude.
2. **Alignment:** desloca a fração menor à direita para igualar os expoentes.
3. **Addition/subtraction:** soma frações de sinais iguais ou subtrai frações
   de sinais diferentes.
4. **Normalization:** trata zeros à esquerda, underflow e carry-out.

## 10. Como o primeiro estágio ordena os operandos?

Compara `exp & frac`. O expoente é comparado primeiro e, em caso de empate, a
fração decide. Isso é coerente para as entradas normalizadas assumidas pelo
livro.

Quando os campos são exatamente iguais, o ramo `else` seleciona o segundo
operando como `big`, inclusive seu sinal.

## 11. O que acontece no alinhamento?

O circuito calcula:

```text
exp_diff = expb - exps
```

Depois desloca `fracs` à direita por essa quantidade. Bits que saem pela
direita são descartados, pois o livro afirma explicitamente que o arredondamento
é ignorado. Diferenças iguais ou maiores que oito zeram completamente a fração
menor.

## 12. Como é feita a soma ou subtração?

```vhdl
sum <= ('0' & fracb) + ('0' & fraca) when signb = signs else
       ('0' & fracb) - ('0' & fraca);
```

Como `big` possui a maior magnitude dentro das hipóteses normalizadas, a
subtração não precisa representar magnitude negativa. O sinal final é `signb`.

## 13. O contador de zeros funciona corretamente?

Para resultados não nulos, sim. Ele retorna:

| Primeiro `1` | `leado` |
|---:|---:|
| `sum(7)` | 0 |
| `sum(6)` | 1 |
| `sum(5)` | 2 |
| `sum(4)` | 3 |
| `sum(3)` | 4 |
| `sum(2)` | 5 |
| `sum(1)` | 6 |
| `sum(0)` | 7 |

O deslocamento `sum_norm` move esse primeiro `1` até a posição 7. Foram
simulados casos com três e sete zeros à esquerda.

## 14. Qual é o problema do contador quando a soma é zero?

O último ramo define `leado=7` tanto para `sum(0)=1` quanto para `sum=0`.
Portanto, o contador não distingue esses dois casos.

Se ocorrer cancelamento exato com `expb >= 7`, a condição
`leado > expb` é falsa e o código executa:

```text
expn = expb - 7
fracn = 0
```

Por exemplo, cancelamento em `expb=8` produz `fraction=0` e `exponent=1`, em
vez de zerar todos os campos de magnitude. Esse é um problema real observado
no código literal.

## 15. O underflow do terceiro exemplo está correto?

Sim, de acordo com o formato do livro:

```text
-0.10000001 × 2^0 + 0.10000000 × 2^0
= -0.00000001 × 2^0
```

Normalizar exigiria deslocar sete posições à esquerda e reduzir o expoente
para `-7`, mas o expoente é sem sinal. O circuito converte a magnitude para
zero. O sinal continua sendo `signb`, logo o Listing pode produzir `-0`. Na
interface da DE10-Lite, os displays mostram `001000`, `LEDR9` permanece aceso
e `LEDR8` apaga para avisar que esse zero veio da perda de um valor não nulo.

## 16. Como o carry é normalizado?

Se `sum(8)=1`, o resultado possui nove bits significativos. O circuito mantém
`sum(8 downto 1)` e incrementa o expoente:

```text
fraction = sum / 2
exponent = expb + 1
```

O quarto exemplo confirma `272 × 2^3 -> 136 × 2^4` nos campos internos.

## 17. O que acontece se já estivermos no expoente 15?

O Listing 3.19 não possui flag nem política de overflow. Como `expn` tem quatro
bits, `15 + 1` retorna para zero. A simulação de duas entradas máximas observa:

```text
sign=0, exponent=0, fraction=255
```

Isso não é saturação e deve ser documentado como limitação do circuito.
Na adaptação para a placa, os displays mostram `0000FF`, mas `LEDR8` apaga para
indicar que essa palavra não é um resultado válido. O núcleo original continua
inalterado; somente a interface física acrescenta o detector.

## 18. O arquivo original foi realmente compilado?

Sim. `utils/adder.vhd` contém a lógica do Listing 3.19 com portas separadas. A
formatação e as aspas tipográficas do texto extraído foram convertidas para
sintaxe VHDL válida, sem alterar a lógica dos estágios.

Execute:

```bash
make original
```

## 19. O que o testbench original verifica?

- os quatro exemplos de sort, align, add/subtract e normalize;
- três zeros à esquerda;
- sete zeros à esquerda exatamente no limite do expoente;
- underflow quando o deslocamento supera o expoente;
- ambiguidade entre soma zero e soma com somente o bit zero;
- carry no expoente máximo.

## 20. Quais sinais devem ser observados no GTKWave?

Principalmente:

```text
signb, signs
expb, exps, exp_diff
fracb, fracs, fraca
sum
leado
sum_norm
expn, fracn
sign_out, exp_out, frac_out
```

`sum`, `leado`, `sum_norm`, `expn` e `fracn` mostram diretamente o quarto
estágio solicitado no enunciado.

## 21. Como abrir a forma de onda original?

```bash
make original
gtkwave build/waves/adder.vcd
```

Isso executa a simulação e abre `build/waves/adder.vcd` no GTKWave. Também é
gerado `build/waves/adder.ghw`.

## 22. Por que existe `adder_unsigned`?

Para implementar o algoritmo diretamente com dois vetores de entrada e um de
saída. `unsigned` é o tipo que transporta os 13 bits; o bit 12 continua sendo
interpretado como sinal. O bloco também fornece `underflow` e `overflow` para
a interface física, evitando repetir a aritmética em `top_fp_adder`.

## 23. A adaptação empacotada mudou o algoritmo?

Não no resultado de 13 bits. A implementação vetorial repete diretamente os
mesmos estágios:

```text
sort -> align -> add/sub -> normalize
```

As flags são uma extensão da Etapa 2: `underflow=1` quando um resultado não
nulo é perdido abaixo do expoente zero, e `overflow=1` quando o carry exigiria
expoente 16. Elas não mudam `res`.

## 24. Como foi comprovado que a adaptação não mudou a lógica?

O testbench de regressão instancia simultaneamente o `fp_adder` original e o
somador vetorial. Todas as 8192 palavras possíveis de `A` são comparadas com 16
amostras de `B`, totalizando 131072 combinações. As saídas coincidiram bit a
bit em todos os casos.

## 25. Qual é a função da pasta `baseline/`?

Preservar a primeira versão criada pelo grupo. A versão ativa retomou essa
estrutura, mas removeu a condição extra `OR sum=0` para manter equivalência
literal com o livro em cancelamentos exatos com expoente maior ou igual a 7.
`utils/adder.vhd` continua sendo a referência original de portas separadas.

## 26. Quais comandos de teste estão disponíveis?

| Comando | Função |
|---|---|
| `make` | quatro testbenches principais e respectivas ondas |
| `make original` | modelo original |
| `make normalization` | exatamente os quatro casos obrigatórios |
| `make packed` | somador vetorial atual e suas flags |
| `make regression` | equivalência original versus somador vetorial |
| `make board` | interface DE10-Lite |
| `make encode INPUT=13.25` | decimal para campos de entrada |
| `make decode DISPLAY=001499 LEDR8=1` | saída `00SEFF` da placa para decimal |
| `make converter-test` | testes das conversões |

## 27. Como gerar e analisar as formas de onda?

```bash
make normalization
gtkwave build/waves/normalization.vcd
```

O Makefile compila `utils/adder.vhd` e
`utils/normalization_testbench.vhd`, simula exatamente os quatro casos e salva
`normalization.vcd` e `normalization.ghw` em `build/waves/`. No GTKWave, devem
ser observados principalmente `sum`, `leado`, `sum_norm`, `expn` e `fracn`.

## 28. Como os operandos são inseridos na DE10-Lite?

`KEY1` confirma e `KEY0` retorna uma etapa:

```text
S1: sign do primeiro operando       em SW9
F1: fraction do primeiro operando   em SW9..SW2
E1: exponent do primeiro operando   em SW9..SW6
S2: sign do segundo operando        em SW9
F2: fraction do segundo operando    em SW9..SW2
E2: exponent do segundo operando    em SW9..SW6
```

`HEX5..HEX4` mostram essas etiquetas. A letra `S` usa o desenho do algarismo
`5`, pois é a aproximação disponível no display de sete segmentos.

## 29. O que aparece nos displays durante a entrada?

- `S1/S2`: `HEX0` mostra `0` ou `1`;
- `F1/F2`: `HEX2..HEX0` mostram a fração em decimal, `000..255`;
- `E1/E2`: `HEX1..HEX0` mostram o expoente em decimal, `00..15`;
- displays sem uso permanecem apagados.

Para um número não nulo normalizado, a fração deve estar entre 128 e 255.

## 30. O que os LEDs mostram durante a entrada?

| Etapa | Chaves | LEDs correspondentes |
|---:|---|---|
| `S1/S2` | `SW9` | `LEDR9` |
| `F1/F2` | `SW9..SW2` | `LEDR9..LEDR2` |
| `E1/E2` | `SW9..SW6` | `LEDR9..LEDR6` |

Os demais LEDs ficam apagados. Durante a entrada, `LEDR8` não significa
“válido”; ele apenas espelha `SW8` quando essa chave pertence ao campo atual.

## 31. Como o resultado aparece nos displays?

Os 13 bits normalizados são mostrados como uma palavra hexadecimal estendida
com zeros:

```text
HEX5 HEX4 HEX3 HEX2 HEX1 HEX0
  0    0    S     E   F[7:4] F[3:0]
```

Exemplo do primeiro caso:

```text
resultado = sign 1, exponent 4, fraction 153 = 0x99
displays  = 001499
LEDR9     = aceso
LEDR8     = aceso
```

Uma palavra de 13 bits precisa de quatro dígitos hexadecimais (`SEFF`). Os dois
primeiros zeros somente completam os seis displays e não fazem parte do dado.

## 32. Qual é o significado dos LEDs no resultado?

- `LEDR9` é `sign_out`: apagado para `0`, aceso para `1`;
- `LEDR8` aceso indica que o resultado é representável;
- `LEDR8` apagado com a palavra hexadecimal visível indica underflow ou
  overflow;
- `LEDR7..0` permanecem apagados.

A palavra nos seis displays distingue `SHOW_RESULT` dos estados de entrada,
que apresentam explicitamente `S1/F1/E1/S2/F2/E2`. O detector separa um zero
exato, que é válido, de um zero produzido pela perda de um resultado não nulo
em underflow.

## 33. Zero sempre deixa `LEDR9` apagado?

Não no código literal do livro. `sign_out` recebe `signb` mesmo quando a
fração normalizada vira zero. Portanto, pode existir zero com `LEDR9` aceso.
Isso não deve ser confundido com uma magnitude negativa diferente de zero; é
uma consequência da representação por sinal e módulo e da implementação do
Listing.

## 34. Por que o resultado não é mais reconstruído como um inteiro grande?

Porque isso usava a fórmula `fraction × 2^exponent`, que difere por um fator
de 256 da definição do livro. A saída atual não reconstrói esse inteiro: apenas
empacota os próprios 13 bits como hexadecimal `00SEFF`. Desse modo, `001499`
significa `1 | 4 | 99` e ainda deve ser decodificado por
`(−1)^sign × (fraction/256) × 2^exponent`.

## 35. O projeto está configurado para a DE10-Lite?

Sim. O QSF seleciona:

- família MAX 10;
- dispositivo `10M50DAF484C7G`;
- clock de 50 MHz em `PIN_P11`;
- dez switches, dez LEDs, `KEY0`, `KEY1` e seis displays;
- `adder_unsigned.vhd`, `hex_to_sseg.vhd` e `top_fp_adder.vhd` no QSF.

## 36. A síntese física já foi validada?

Ainda não neste ambiente, que não possui Quartus nem acesso à placa. O grupo
deve registrar:

- compilação completa no Quartus;
- relatório de timing;
- utilização de recursos;
- geração e programação do `.sof`;
- testes dos quatro exemplos e dos limites da normalização;
- fotografias ou vídeo da placa.

## 37. Como a inteligência artificial foi utilizada?

O Codex foi usado para revisar o formato, comparar a implementação com o
material do livro, criar testbenches, automatizar GHDL, adaptar a interface da
DE10-Lite e documentar as decisões. Uma interpretação provisória baseada em
`k × 2^e` foi posteriormente rejeitada após a conferência de `0.f × 2^e`.
Esse histórico está preservado em `docs/AI_AUDIT.md`.

## 38. Qual foi a contribuição da IA e quais são seus limites?

A IA acelerou a criação dos testes e detectou os casos de cancelamento exato e
overflow do expoente. Entretanto, não executou a síntese física no Quartus nem
os testes na placa. A responsabilidade técnica e a validação final são do
grupo.

## 39. Como registrar as contribuições pela taxonomia CRediT?

Cada integrante deve receber somente os papéis correspondentes às atividades
que realizou. Papéis relevantes podem incluir:

- Conceptualization;
- Formal analysis;
- Investigation;
- Methodology;
- Software;
- Validation;
- Visualization;
- Writing – original draft;
- Writing – review & editing;
- Project administration.

Os nomes, papéis e justificativas já estão preenchidos no README e em
`docs/CREDIT.md` conforme as responsabilidades informadas pelo grupo.

## 40. O que falta para concluir o projeto?

1. capturar e interpretar `sum`, `leado`, `sum_norm`, `expn` e `fracn` no
   GTKWave;
2. compilar no Quartus e revisar warnings e timing;
3. programar e testar a DE10-Lite;
4. registrar os casos críticos e as limitações encontradas;
5. adicionar as reflexões individuais sobre o uso da IA;
6. publicar o repositório privado e enviar o link no Moodle.

## 41. O aviso de síntese sobre vetor não numérico indica erro?

O GHDL avisa sobre a comparação literal do livro:

```vhdl
(exp1 & frac1) > (exp2 & frac2)
```

As concatenações são `std_logic_vector` e a comparação é lexicográfica, o que
produz a mesma ordenação binária sem sinal para palavras de igual largura. O
GHDL conclui a síntese, mas emite o aviso `comparing non-numeric vector is
unexpected`. A expressão foi preservada para manter o Listing 3.19.
Uma chamada direta a `ghdl --synth` aceita o circuito apesar do aviso. A
compilação no Quartus continua sendo a validação física exigida.

## 42. Como converter diretamente a saída hexadecimal da placa?

Copie os seis displays no formato `00SEFF`. Por exemplo, para `001499`:

```bash
make decode DISPLAY=001499 LEDR8=1
```

O script interpreta `s=1`, `e=0x4=4` e `f=0x99=153`, monta a palavra
`1 0100 10011001`, informa que `LEDR9` deve estar aceso e calcula:

```text
−(153/256) × 2^4 = −9.5625
```

O formato tem exatamente seis dígitos: os dois zeros de extensão, um dígito de
sinal, um de expoente e dois de fração. Informe também `LEDR8=1` ou `LEDR8=0`.
Sem esse LED, `001000` não permite distinguir cancelamento exato de underflow,
e `0000FF` não permite distinguir `0.99609375` válido de overflow.
