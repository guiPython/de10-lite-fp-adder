# Checklist orientado pela rubrica

Este documento não atribui nota antecipadamente. Ele relaciona cada requisito
de 2 pontos com evidências verificáveis e destaca o que ainda depende do grupo.

## 1. Interpretação dos dados e validação — alvo: 2/2

### Evidências prontas

- fórmula correta `(-1)^s × (f/256) × 2^e`;
- procedimento nos dois sentidos em `CONVERSAO_NUMERICA.md`;
- exemplos exatos, truncado, limites e valor fora da faixa;
- script de conferência e nove testes automatizados;
- saída física `E<e> F<ff>` ligada diretamente aos 13 bits.

### Antes da apresentação

- [ ] cada integrante converte um decimal para 13 bits sem consultar o script;
- [ ] cada integrante converte `1 0100 10011001` para `−9.5625`;
- [ ] o grupo explica por que `50000` não cabe;
- [ ] o grupo explica o erro de `3.14 → 3.125`.

## 2. Adaptação de hardware — alvo: 2/2

### Evidências prontas

- diagrama de blocos consistente com `top_fp_adder.vhd`;
- diagrama dos quatro estágios;
- máquina de estados `S1/F1/E1/S2/F2/E2`;
- tabela de motivos para cada adaptação;
- mapeamento completo de clock, botões, switches, LEDs e displays;
- pinos conferidos com o material da Terasic e botões configurados como
  entradas Schmitt trigger;
- testbench da interface física;
- conferência local de sintetizabilidade do topo com GHDL.

### Pendente na ferramenta/placa

- [ ] captura do Pin Planner consistente com a tabela;
- [ ] captura da compilação e utilização de recursos;
- [ ] foto/vídeo da entrada e saída na DE10-Lite;
- [ ] quatro casos físicos executados e interpretados.

## 3. Simulação e código VHDL — alvo: 2/2

### Evidências prontas

- `normalization_testbench.vhd` contém exatamente os quatro casos;
- cada caso ocupa 20 ns e possui `assert`;
- figura gerada do VCD com `sum`, `leado`, `sum_norm`, `expn` e `fracn`;
- explicação matemática caso a caso;
- código original separado do wrapper adaptado;
- regressão de equivalência em 131072 combinações.

### Evidência final a inserir

- [ ] salvar uma captura legível do GTKWave com os quatro intervalos;
- [ ] inserir a captura e legenda no relatório final.

## 4. Diário de IA e gestão — alvo: 2/2

### Evidências prontas

- registro técnico dos prompts consolidados, critérios e decisões;
- erro inicial `k×2^e` documentado, rejeitado e corrigido;
- justificativa humana para aceitar/rejeitar sugestões;
- validações que sustentam cada decisão;
- limitações da IA explicitadas;
- modelo CRediT com definição e evidência.

### Pendente do grupo

- [x] adicionar nomes reais;
- [x] preencher atividades e papéis conforme as responsabilidades informadas;
- [ ] cada integrante escrever uma reflexão curta sobre aprendizagem;
- [ ] exportar/anexar a conversa, caso exigido.

## 5. Organização e reprodutibilidade — alvo: 2/2

### Evidências prontas

- README como página inicial;
- tutorial do zero até a placa;
- comandos automatizados no Makefile;
- documentos especializados ligados entre si;
- seção de problemas comuns;
- checklist de evidências com nomes padronizados.

### Revisão final

- [ ] testar o tutorial em uma máquina limpa ou com outro integrante;
- [x] remover todos os marcadores `[Nome]` e `[papéis]` do README e do CRediT;
- [ ] conferir todos os links e imagens no GitHub;
- [ ] confirmar que nenhum resultado físico pendente é declarado como pronto;
- [ ] enviar o link privado correto no Moodle.

## Definição de pronto para potencial 10/10

O repositório estará completo somente quando todos os itens acima estiverem
marcados, principalmente GTKWave, Quartus, placa e reflexões dos integrantes.
A documentação não substitui essas evidências práticas.
