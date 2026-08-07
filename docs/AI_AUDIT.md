# Auditoria do uso de inteligência artificial

## Ferramenta e método

**Ferramenta:** Codex, OpenAI.
**Uso:** revisão matemática, VHDL, testbenches, interface, automação e
documentação.

Fluxo adotado pelo grupo:

1. definir requisito e resultado esperado;
2. solicitar análise ou alteração verificável;
3. comparar com o Listing 3.19 e o hardware da DE10-Lite;
4. executar cálculos, `assert`, regressão ou síntese;
5. aceitar, corrigir ou rejeitar a sugestão.

As formulações abaixo resumem objetivos técnicos da conversa; não são
transcrições literais. A conversa original deve ser anexada sem edição caso a
disciplina exija os prompts integrais.

## Objetivos enviados à IA

| ID | Objetivo | Critério definido pelo grupo |
|---:|---|---|
| P1 | conferir o formato `(-1)^S×(F/256)×2^E` | coincidir com o livro |
| P2 | compilar o núcleo original sem corrigir seus limites | preservar o comportamento observado |
| P3 | testar align/subtract, shift esquerdo, underflow e carry | quatro casos com `assert` e sinais internos |
| P4 | manter entradas e saída de 13 bits | somente o carry interno usa 9 bits |
| P5 | adaptar para vetores e provar equivalência | comparar `res` bit a bit com o original |
| P6 | usar `S1/F1/E1/S2/F2/E2` na DE10-Lite | configurar 26 bits com 10 switches |
| P7 | mostrar `00SEFF`, sinal e validade | conferir displays e LEDs no testbench |
| P8 | automatizar testes e conversões | comandos reproduzíveis no Makefile |

## Erro identificado e correção humana

A primeira solução adotou `F×2^E`, uma soma interna de 25 bits e considerou
`50000` aproximadamente representável. Essa hipótese não correspondia ao
Listing 3.19, que usa `0.F=F/256`.

O grupo detectou a divergência ao comparar a fórmula, a largura da saída e o
quarto estágio com o trecho original. A correção foi:

- restaurar entradas e saída de 13 bits;
- usar somente 9 bits na soma temporária das frações;
- manter `utils/adder.vhd` como referência do livro;
- implementar os mesmos quatro estágios em `adder_unsigned.vhd`;
- comparar 131072 combinações entre as duas versões;
- mostrar diretamente a palavra `00SEFF`, sem reconstruir `F×2^E`.

Esse episódio mostrou que testes de uma hipótese errada não validam a
especificação. O livro e a derivação matemática tiveram prioridade.

## Decisões avaliadas

| Sugestão | Decisão | Evidência |
|---|---|---|
| soma de 25 bits e `F×2^E` | rejeitada | contradiz o livro |
| interface empacotada de 13 bits | aceita | regressão de 131072 casos |
| corrigir silenciosamente o Listing original | rejeitada | a Etapa 1 exige fidelidade |
| flags de underflow/overflow na adaptação | aceita | casos dirigidos e `LEDR8` |
| FSM de seis campos | aceita | testbench de `top_fp_adder` |
| saída hexadecimal `00SEFF` | aceita | VCD, SVG e conversor |
| figura gerada do VCD | aceita | valores vinculados à simulação |

## Evidências executáveis

| Comando | O que comprova |
|---|---|
| `make original` | núcleo do livro |
| `make normalization` | quatro casos do quarto estágio |
| `make packed` | somador vetorial e flags |
| `make regression` | equivalência de `res` em 131072 pares |
| `make board` | FSM, botões, chaves, LEDs e displays |
| `make converter-test` | conversões e validade |
| `make board-svg` | painéis reconstruídos do VCD |

Resultados observados: 7 casos originais, 4 de normalização, 11 do somador
vetorial, 131072 comparações, interface da placa e 10 testes do conversor
aprovados.

## Arquivos apoiados pela IA

- VHDL e testes: `adder_unsigned*`, `top_fp_adder*`, `hex_to_sseg.vhd` e
  arquivos em `utils/`;
- Quartus: `top_fp_adder.qpf`, `.qsf` e `.sdc`;
- automação: `Makefile` e scripts em `scripts/`;
- documentação: `README.md` e pasta `docs/`.

## Responsabilidade e limites

A IA não opera fisicamente a placa. O grupo é responsável por:

- conferir todas as alterações;
- executar o Quartus e analisar warnings/timing;
- programar e testar a DE10-Lite;
- inserir capturas e fotos reais;
- explicar a conversão e os quatro ramos sem depender do script.

Antes da entrega, cada integrante deve acrescentar uma reflexão pessoal curta:
o que aprendeu, qual sugestão verificou e qual limitação encontrou. O registro
CRediT está em [CREDIT.md](CREDIT.md).
