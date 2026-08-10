# Auditoria do uso de inteligência artificial

## Ferramenta e método

**Ferramenta:** Codex (OpenAI).  
**Formato de Registro:** Conversa mantida em sessão única. O PDF na íntegra com todos os prompts e respostas originais está anexado no repositório como `docs/Conversa_Codex_Auditoria.pdf`.

### Exemplos de Prompts-Chave Utilizados:
1. **P1 (Validação Teórica):** 
   > "Verifique se a representação do formato (-1)^S × (F/256) × 2^E está de acordo com a especificação do Listing 3.19 do livro-texto para o somador de ponto flutuante."
2. **P3 (Geração de Testbench):** 
   > "Escreva um testbench em VHDL que avalie os quatro estágios de normalização (align/subtract, shift esquerdo, underflow e carry), incluindo verificações com 'assert' e sinais internos."
3. **P8 (Automação):** 
   > "Crie regras no Makefile para automatizar a regressão de 131.072 combinações de teste e gerar relatórios executáveis de erro."

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
| P8 | automatizar testes, conversões e previsão do erro | comandos reproduzíveis no Makefile |

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
| `make result A=5000 B=1000` | resolução, alinhamento e erro decimal acumulado |
| `make board-svg` | painéis reconstruídos do VCD |

Resultados observados: 7 casos originais, 4 de normalização, 11 do somador
vetorial, 131072 comparações, interface da placa e 16 testes do conversor
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

  ## Impacto do uso da IA na Aprendizagem e no Projeto

A ferramenta Codex atuou como um **assistente de automação e revisão**, trazendo impacto positivo em tarefas repetitivas, mas exigindo controle conceitual do grupo em arquitetura de hardware:

* **Onde a IA mais ajudou (Produtividade):** 
  * Geração rápida de *testbenches* extensos e regras de automação via `Makefile`.
  * Criação dos scripts de suporte (`scripts/`) e conversores de visualização (`board-svg`).
  * Estruturação e organização inicial da documentação técnica.

* **Onde a IA falhou e o que o grupo aprendeu (Ganho Conceitual):**
  * A IA tentou "otimizar" a arquitetura alterando a precisão interna para 25 bits e redefinindo a fórmula matemática para $F \times 2^E$.
  * O grupo aprendeu que **simulações e testes automatizados não garantem a correção teórica se a premissa estiver errada**. A análise crítica do Listing 3.19 e os cálculos manuais prevaleceram sobre as sugestões de código da IA.
