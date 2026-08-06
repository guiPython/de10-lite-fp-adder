# Auditoria do uso de inteligência artificial

## 1. Ferramenta e finalidade

- **Ferramenta:** Codex, OpenAI.
- **Datas da sessão:** 5 e 6 de agosto de 2026.
- **Escopo:** revisão do algoritmo, adaptação VHDL, elaboração de testbenches,
  interface da DE10-Lite, automação e documentação.

A IA foi utilizada como ferramenta de revisão e apoio à implementação. As
decisões de arquitetura não foram delegadas: o grupo definiu a especificação,
comparou as respostas com o Listing 3.19, executou os testes e aceitou ou
rejeitou cada sugestão com base em evidências.

O procedimento adotado foi:

1. formular a hipótese ou requisito técnico;
2. solicitar uma análise ou implementação verificável;
3. comparar a resposta com o material do livro e o manual da placa;
4. executar testbenches autochecking;
5. aceitar, corrigir ou rejeitar a sugestão;
6. registrar a decisão e sua justificativa.

## 2. Prompts técnicos consolidados

Os prompts abaixo são consolidações fiéis dos objetivos enviados durante a
conversa, com ortografia e terminologia normalizadas para o relatório. Eles não
são apresentados como transcrição literal. A conversa completa pode ser
anexada em PDF para permitir a auditoria dos textos originais.

| ID | Prompt técnico consolidado | Critério de aceitação definido pelo grupo |
|---:|---|---|
| P01 | “Compare a implementação com o formato do Listing 3.19: `(-1)^s × 0.f × 2^e`, com 1 bit de sinal, 4 de expoente e 8 de fração.” | fórmula, faixa e campos devem coincidir com o livro |
| P02 | “Compile o núcleo original sem corrigir silenciosamente seu comportamento e analise os quatro estágios: sort, align, add/sub e normalize.” | o arquivo original deve passar no GHDL e manter seus casos-limite observáveis |
| P03 | “Crie um testbench autochecking com exatamente os quatro casos exigidos: alinhamento/subtração, normalização à esquerda, underflow e carry.” | quatro intervalos claros, resultados calculados e `assert` em todos os casos |
| P04 | “Mantenha entradas e saída com 13 bits; use apenas um nono bit temporário para o carry da fração.” | nenhuma soma interna de 25 bits e saída final de 13 bits |
| P05 | “Use `adder_unsigned` apenas como wrapper de dois vetores de 13 bits e prove equivalência com o núcleo de portas separadas.” | igualdade bit a bit entre wrapper e Listing 3.19 |
| P06 | “Adapte a entrada para `S1, F1, E1, S2, F2, E2`, usando `SW9` como início de todos os campos e botões para avançar ou retornar.” | todos os 26 bits devem ser configuráveis com dez switches |
| P07 | “Durante a entrada, apresente fração e expoente em decimal e espelhe nos LEDs os bits dos switches ativos.” | leitura humana e conferência binária simultâneas |
| P08 | “Na saída, mostre os campos como `E<expoente> F<fração>`, use `LEDR9` para o sinal, `LEDR8` para validade e mantenha os demais LEDs apagados.” | a interface deve expor diretamente os 13 bits, sem fator incorreto de 256 |
| P09 | “Automatize os testbenches, salve VCD/GHW e crie `encode/decode` entre decimal e os campos usados na placa.” | testes reproduzíveis e conversão comprovada nos dois sentidos |
| P10 | “Investigue `leado=7`, cancelamento exato e carry em expoente 15, documentando limitações sem modificar o núcleo da Etapa 1.” | comportamento literal separado de uma eventual correção futura |
| P11 | “Organize o README conforme o template da disciplina, incluindo diagramas, evidências, análise crítica da IA e CRediT.” | correspondência direta com os cinco critérios da rubrica |

Essa formulação deixa explícitos o objetivo, a hipótese e a evidência esperada.
As perguntas exploratórias da conversa serviram para confrontar interpretações
possíveis; as decisões finais foram tomadas somente depois da leitura do
material original e da execução dos testes.

## 3. Decisões técnicas tomadas pelo grupo

### 3.1 Definição do formato numérico

Foram comparadas duas interpretações:

```text
Hipótese provisória: k × 2^e
Definição do livro:  (-1)^s × 0.f × 2^e
```

O trecho do capítulo 3.7.4 fornecido pelo grupo confirmou que `0.f=f/256`.
Assim, `fraction=195` e `exponent=8` representam `195`, não `49920`, e
`50000` está fora da faixa do formato. A hipótese provisória foi rejeitada.

### 3.2 Largura externa e precisão intermediária

O grupo determinou que os dois operandos e o resultado devem ter 13 bits. O
único bit adicional necessário é `sum(8)`, usado temporariamente para o carry
da soma de duas frações de 8 bits. A proposta inicial de uma soma de 25 bits
não reproduzia o algoritmo do livro e foi removida.

### 3.3 Interface empacotada

`adder_unsigned.vhd`, criado por Guilherme Rocha Muzi Franco, foi mantido
porque reduz a quantidade de portas sem modificar a representação. O wrapper
separa `sign`, `exponent` e `fraction`, instancia `fp_adder` e concatena os
mesmos campos na saída. A aceitação foi baseada em uma regressão de 131072
comparações bit a bit.

### 3.4 Interface física da DE10-Lite

Guilherme Rocha Muzi Franco e Lucas Marques de Oliveira desenvolveram
`top_fp_adder.vhd`. Como a placa não permite configurar simultaneamente 26 bits
com seus dez switches, foi adotada a sequência `S1/F1/E1/S2/F2/E2`.

As escolhas de interface foram deliberadas:

- todos os campos começam em `SW9`;
- `KEY1` confirma e `KEY0` retorna;
- os displays mostram o campo em decimal durante a entrada;
- os LEDs espelham os bits configurados;
- o resultado mostra `E<e> F<ff>`;
- `LEDR9` representa o sinal e `LEDR8` indica resultado apresentado.

Lucas configurou o ambiente e os arquivos do projeto Quartus. Os botões foram
configurados como entradas `3.3 V SCHMITT TRIGGER`, enquanto clock, switches,
LEDs e displays usam `3.3-V LVTTL`.

### 3.5 Automação e conversão

Guilherme criou o Makefile de automação dos testbenches e os scripts de
conversão:

- `scripts/fp13.py encode`: decimal para os campos de entrada;
- `scripts/fp13.py decode`: campos da saída da placa para decimal;
- `scripts/fp13.py decode-hex`: leitura direta de `LEDR9` e dos displays no
  formato `E<e> F<ff>` para decimal;
- `scripts/test_fp13.py`: testes de valores exatos, truncamento e limites;
- `scripts/vcd_to_wave_svg.py`: figura dos quatro casos gerada do VCD.

## 4. Erro da IA e correção humana

### Erro principal

A IA aceitou inicialmente a hipótese `k × 2^e` e propôs uma soma interna de 25
bits com quantização posterior. Essa solução era coerente com a hipótese
provisória, mas incompatível com a especificação real `0.f × 2^e` e com o
quarto estágio do Listing 3.19.

### Como o grupo detectou o erro

O grupo observou que a largura e a fórmula não correspondiam ao material da
atividade, forneceu o trecho original do livro e exigiu que:

1. as entradas e a saída permanecessem com 13 bits;
2. a fração fosse interpretada como `f/256`;
3. a normalização reproduzisse o Listing 3.19;
4. o wrapper fosse comparado diretamente com o núcleo original.

### Correção adotada

O núcleo de 25 bits foi removido. `adder_unsigned` passou a ser somente um
wrapper de `fp_adder`, a saída da placa foi alterada para `E<e> F<ff>` e uma
regressão confirmou 131072 correspondências. A sugestão da IA só foi aceita
depois dessa correção e da validação automática.

Esse episódio mostrou que uma implementação pode passar em testes internos e
ainda estar errada em relação à especificação. A fonte primária e a derivação
matemática tiveram prioridade sobre a resposta da IA.

## 5. Análise crítica das sugestões

| Sugestão ou decisão | Decisão humana | Justificativa | Evidência |
|---|---|---|---|
| interpretar o campo como `k×2^e` e usar 25 bits | rejeitada | contradizia `0.f×2^e` | capítulo 3.7.4 e novos testes |
| considerar `−129+128=−1` representável | rejeitada no formato final | a diferença fica abaixo da menor magnitude normalizada | caso 3 |
| empacotar as portas em vetores de 13 bits | aceita | reduz portas sem mudar campos ou matemática | regressão de equivalência |
| mostrar inteiro reconstruído nos seis displays | rejeitada | introduzia fator incorreto de 256 | saída `E<e> F<ff>` |
| usar etiquetas, decimal e LEDs durante a entrada | aceita | melhora operação sem alterar o somador | testbench de `top_fp_adder` |
| corrigir zero e overflow do Listing na Etapa 1 | rejeitada | a atividade exige analisar o original | limitações documentadas |
| gerar figura diretamente do VCD | aceita | mantém a evidência ligada à simulação | `vcd_to_wave_svg.py` |

## 6. Conhecimento técnico demonstrado

1. **Ponto binário:** `0.f` equivale a `f/256`; ignorá-lo altera toda a faixa.
2. **Largura interna e externa:** o carry exige 9 bits temporários, mas a
   interface continua com 13 bits.
3. **Normalização:** zeros à esquerda, underflow e carry seguem ramos distintos.
4. **Fidelidade:** a Etapa 1 deve preservar até as limitações do código do
   livro, em vez de corrigi-las silenciosamente.
5. **Equivalência:** o wrapper é válido porque coincide bit a bit com o original.
6. **Reprodutibilidade:** cada resultado relevante possui comando, `assert` e
   forma de onda correspondente.
7. **Separação de evidências:** GHDL/GTKWave, Quartus e placa validam etapas
   diferentes e não são intercambiáveis.

## 7. Verificação das decisões

| Comando | Evidência produzida |
|---|---|
| `make original` | sete comportamentos do modelo original |
| `make normalization` | quatro casos obrigatórios em 80 ns e VCD/GHW |
| `make packed` | onze casos dirigidos do wrapper |
| `make board` | FSM, switches, botões, LEDs e displays |
| `make regression` | 131072 comparações original versus wrapper |
| `make encode`, `make decode` e `make decode-hex` | conversão entre decimal, campos e saída da placa |
| `make converter-test` | nove testes de conversão, hexadecimal e limites |
| `python3 scripts/vcd_to_wave_svg.py ...` | figura reconstruída do VCD |

Também foi realizada uma conferência de sintetizabilidade com `ghdl --synth`.
O aviso sobre a comparação de `std_logic_vector` em `exp & frac` foi mantido
porque essa expressão pertence ao código literal do livro.

## 8. Resultados observados

- compilação VHDL-2008 concluída no GHDL;
- sete comportamentos do núcleo original aprovados;
- quatro casos obrigatórios de normalização aprovados;
- onze casos dirigidos do wrapper aprovados;
- 131072 comparações de equivalência aprovadas;
- interface da DE10-Lite aprovada em testbench;
- nove testes do conversor aprovados;
- VCD, GHW e figura de normalização gerados automaticamente.

## 9. Arquivos produzidos ou revisados com auxílio da IA

### VHDL e FPGA

- `utils/adder.vhd` e seus testbenches;
- `adder_unsigned.vhd` e seus testbenches;
- `top_fp_adder.vhd` e seu testbench;
- `hex_to_sseg.vhd`;
- `top_fp_adder.qpf`, `top_fp_adder.qsf` e `top_fp_adder.sdc`;

### Automação e documentação

- `Makefile`;
- `scripts/fp13.py`, `scripts/test_fp13.py` e `scripts/vcd_to_wave_svg.py`;
- `README.md` e os documentos da pasta `docs/`.

O uso de IA não elimina a autoria nem a responsabilidade técnica declarada na
[Taxonomia CRediT](CREDIT.md). A IA apoiou a revisão e a redação; o grupo
determinou requisitos, selecionou soluções e validou os resultados.

## 10. Limitações e responsabilidade

A IA não teve acesso físico à placa e não substitui a verificação no Quartus
ou na DE10-Lite. A captura interpretada do GTKWave, os relatórios de síntese e
as fotos dos quatro testes físicos devem ser adicionados pelo grupo após a
execução real.

Se a conversa completa for exportada em PDF, ela deve ser anexada sem edição
como evidência complementar. Este diário organiza tecnicamente as decisões,
mas não substitui o registro integral quando ele for solicitado.
