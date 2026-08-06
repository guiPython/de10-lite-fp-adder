# Tutorial reproduzível do projeto

Este roteiro foi escrito para que uma pessoa iniciante consiga reproduzir o
projeto desde a representação numérica até a programação da DE10-Lite.

## 1. Resultado esperado

Ao final, será possível:

1. converter números decimais para o formato normalizado de 13 bits;
2. compilar o VHDL original do livro;
3. observar os quatro casos de normalização;
4. comprovar que o somador vetorial não altera a lógica do livro;
5. simular a interface física;
6. compilar no Quartus e programar a DE10-Lite;
7. interpretar os displays e voltar ao valor decimal.

## 2. Ferramentas

Necessárias para a simulação aberta:

- GHDL com suporte a VHDL-2008;
- GTKWave;
- GNU Make;
- Python 3, somente para conferir conversões e gerar a figura do VCD.

Necessárias para a entrega física:

- Intel Quartus compatível com MAX 10;
- driver USB-Blaster;
- placa DE10-Lite e cabo USB.

Confirme as ferramentas de terminal:

```bash
ghdl --version
gtkwave --version
make --version
python3 --version
```

## 3. Obtenção e estrutura

Depois de clonar ou extrair o repositório, entre na pasta que contém o
`Makefile`:

```bash
cd de10-lite-fp-adder
make help
```

Arquivos essenciais:

```text
utils/adder.vhd                         modelo do livro
utils/normalization_testbench.vhd       quatro casos obrigatórios
adder_unsigned.vhd                      somador vetorial de 13 bits
top_fp_adder.vhd                        interface DE10-Lite
top_fp_adder.qpf/.qsf/.sdc              projeto Quartus
```

## 4. Compreensão do formato antes da simulação

Leia [CONVERSAO_NUMERICA.md](CONVERSAO_NUMERICA.md). Resolva manualmente pelo
menos os exemplos `13.25`, `−9.5625` e `3.14`, depois confira:

```bash
make encode INPUT=13.25
make decode DISPLAY=001499 LEDR8=1
make converter-test
```

Não prossiga enquanto não estiver claro que:

```text
value = (-1)^sign × (fraction/256) × 2^exponent
```

`fraction=195` e `exponent=8` representam `195`, não `49920`.

## 5. Etapa 1 — modelo original

Compile e simule o Listing 3.19:

```bash
make original
```

Resultado esperado no terminal:

```text
Original book implementation: all 7 observed behaviors passed.
```

Esse alvo gera:

```text
build/waves/adder.vcd
build/waves/adder.ghw
```

O arquivo `utils/adder.vhd` usa portas separadas e preserva os sinais internos
do livro. Ele deve ser apresentado antes da adaptação.

## 6. Quatro casos obrigatórios

Execute o testbench dedicado:

```bash
make normalization
```

Resultado esperado:

```text
All four required normalization cases passed.
```

Abra a onda:

```bash
gtkwave build/waves/normalization.vcd
```

Leia [VALIDACAO_SIMULACAO.md](VALIDACAO_SIMULACAO.md) enquanto observa:

- `sum`;
- `leado`;
- `sum_norm`;
- `expn`;
- `fracn`;
- `case_index`.

Os casos ocupam intervalos fixos de 20 ns, o que evita imagens com transições
amontoadas.

## 7. Análise das formas de onda no GTKWave

Gere e abra a forma de onda dos quatro casos:

```bash
make normalization
gtkwave build/waves/normalization.vcd
```

Na árvore de sinais, expanda `normalization_testbench/uut` e apresente:

1. `sum`, resultado de 9 bits da soma ou subtração;
2. `leado`, quantidade de zeros à esquerda;
3. `sum_norm`, fração depois do deslocamento;
4. `expn` e `fracn`, campos normalizados;
5. `case_index`, identificador dos quatro intervalos.

Salve uma captura legível como
`docs/evidence/gtkwave-normalization.png`. A imagem deve mostrar a escala de
`0–80 ns`, os nomes dos sinais e os quatro casos. Explique cada intervalo em
vez de inserir uma imagem sem interpretação.

## 8. Etapa 2 — adaptação sem mudar a matemática

Execute:

```bash
make packed
make regression
```

`adder_unsigned.vhd` implementa os mesmos quatro estágios usando:

```text
a, b: vetores de 13 bits
res: vetor de 13 bits
underflow, overflow: flags de faixa
```

A regressão compara o somador vetorial e o modelo original em 131072
combinações. O resultado esperado é:

```text
Equivalence regression completed: all 131072 combinations matched the book core.
```

Esse teste é a evidência de que a adaptação de portas não alterou a lógica.

## 9. Interface da DE10-Lite em simulação

```bash
make board
gtkwave build/waves/top_fp_adder.vcd
```

O testbench simula:

- sequência `S1, F1, E1, S2, F2, E2`;
- pulsos ativos em zero nos botões;
- pré-visualização decimal;
- espelhamento binário nos LEDs;
- resultado empacotado `00SEFF` nos seis displays;
- sinal em `LEDR9` e validade em `LEDR8`, que apaga no underflow ou overflow.

Consulte [HARDWARE_DE10_LITE.md](HARDWARE_DE10_LITE.md) para os diagramas,
pinout e justificativas de cada adaptação.

## 10. Verificação completa no GHDL

```bash
make
```

Esse comando executa os quatro testbenches principais e guarda as formas de
onda em `build/waves/`:

- modelo original;
- somador vetorial de 13 bits;
- interface da placa;
- quatro casos obrigatórios.

A regressão exaustiva é opcional porque não gera uma forma de onda útil:

```bash
make regression
```

O conversor e a figura são conferidos separadamente:

```bash
make converter-test
python3 scripts/vcd_to_wave_svg.py \
    build/waves/normalization.vcd \
    docs/images/four-normalization-cases.svg
make board-svg
```

Qualquer falha interrompe o comando com código diferente de zero.

## 11. Criação e compilação no Quartus

1. Abra o Quartus.
2. Selecione **File → Open Project**.
3. Abra `top_fp_adder.qpf`.
4. Confirme em **Assignments → Device** o dispositivo `10M50DAF484C7G`.
5. Confirme em **Assignments → Pin Planner** os pinos descritos em
   `HARDWARE_DE10_LITE.md`.
6. Execute **Processing → Start Compilation**.
7. Verifique se não existem erros.
8. Abra **Compilation Report → Fitter → Resource Section** e registre recursos.
9. Abra o relatório do TimeQuest e confira o clock de 20 ns.
10. Salve capturas da compilação, do Pin Planner e do timing em
    `docs/evidence/`.

Pelo terminal do Quartus:

```bash
quartus_sh --flow compile top_fp_adder
```

Não confunda “GHDL passou” com “Quartus sintetizou”: são evidências diferentes.

## 12. Programação da placa

1. Conecte a DE10-Lite e ligue a alimentação.
2. Abra **Tools → Programmer**.
3. Em **Hardware Setup**, selecione o USB-Blaster.
4. Se necessário, use **Auto Detect** e selecione o MAX 10 correto.
5. Adicione `output_files/top_fp_adder.sof`.
6. Marque **Program/Configure**.
7. Clique em **Start** e aguarde 100%.

Registre uma captura do Programmer concluído.

## 13. Operação física

Para cada operando:

1. em `S`, configure `SW9` e confirme com `KEY1`;
2. em `F`, configure `SW9..SW2`, confira o binário nos LEDs e o decimal nos
   displays, depois confirme;
3. em `E`, configure `SW9..SW6`, confira LEDs e displays e confirme.

Depois de `E2`, leia:

```text
00SEFF = 00 | sign | exponent | fraction
LEDR9 = sign
LEDR8 = 1 para resultado válido; 0 para underflow ou overflow
```

Converta os campos de volta para decimal antes de afirmar que a soma está
correta.

## 14. Teste físico obrigatório

Execute os quatro casos da tabela em `HARDWARE_DE10_LITE.md`. Para cada caso:

1. fotografe uma etapa de entrada mostrando switches, LEDs e displays;
2. fotografe o resultado;
3. anote os 13 bits produzidos;
4. converta o resultado para decimal;
5. compare com o cálculo manual;
6. explique o ramo de normalização utilizado.

## 15. Evidências e entrega

Use [evidence/README.md](evidence/README.md) para nomear as capturas. Antes da
entrega, confira [RUBRICA_CHECKLIST.md](RUBRICA_CHECKLIST.md).

Não deixe marcadores sem preencher:

- nomes dos integrantes;
- papéis CRediT;
- captura interpretada do GTKWave;
- relatórios do Quartus;
- fotos da placa;
- observações pessoais sobre o uso da IA.

## 16. Problemas comuns

| Sintoma | Verificação |
|---|---|
| `ghdl: command not found` | instalação do GHDL e `PATH` |
| GTKWave abre sem sinais | execute primeiro `make normalization` |
| resultado decimal 256 vezes maior | foi usado `f×2^e` em vez de `(f/256)×2^e` |
| entrada não normalizada | para número não nulo, `fraction` deve ser ≥128 |
| botão avança mais de uma vez | confirme clock, sincronizador e hardware dos botões |
| display invertido | segmentos da DE10-Lite são ativos em zero |
| resultado zero com sinal aceso | o Listing preserva `signb`; consulte a análise crítica |
| aviso `comparing non-numeric vector` | o Listing compara `exp & frac` literalmente; a comparação é lexicográfica e o GHDL ainda gera o circuito |
| Quartus não encontra uma entidade | confira os três arquivos VHDL listados no QSF |
