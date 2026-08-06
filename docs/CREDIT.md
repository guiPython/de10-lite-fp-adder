# Contribuições da equipe — Taxonomia CRediT

As contribuições foram classificadas segundo a
[Contributor Role Taxonomy (CRediT)](https://credit.niso.org/contributor-roles-defined/).
A taxonomia possui 14 papéis possíveis; abaixo aparecem somente os papéis
compatíveis com as atividades efetivamente atribuídas a cada integrante.

CRediT descreve tipos de contribuição e não determina autoria nem porcentagem
de trabalho. Um mesmo papel pode ser compartilhado quando mais de uma pessoa
participou daquela atividade.

## Distribuição das responsabilidades

| Integrante | Responsabilidade principal | Entregas associadas |
|---|---|---|
| **Guilherme Rocha Muzi Franco** | Algoritmo, simulação e desenvolvimento VHDL | explicação do algoritmo, cálculos, casos de teste, `adder_unsigned.vhd`, desenvolvimento compartilhado de `top_fp_adder.vhd` e validação matemática |
| **Lucas Marques de Oliveira** | Interface da DE10-Lite e ambiente Quartus | desenvolvimento compartilhado de `top_fp_adder.vhd`, investigação do funcionamento, configuração do Quartus e recursos necessários para a FPGA |
| **Marconde Correia Pinho** | Documentação e auditoria da IA | documentação no GitHub, organização do relatório e registro do uso de inteligência artificial |

## Papéis CRediT por integrante

### Guilherme Rocha Muzi Franco — Algoritmo, Simulação e Desenvolvimento VHDL

- **Conceptualization:** compreensão do problema e formulação dos objetivos de
  validação do somador de ponto flutuante simplificado.
- **Methodology:** definição da estratégia de simulação e dos casos necessários
  para exercitar ordenação, alinhamento, soma/subtração e normalização.
- **Formal analysis:** conversão entre decimal e o formato normalizado de 13
  bits, conferência matemática dos resultados, underflow e carry-out.
- **Investigation:** investigação do funcionamento do circuito em conjunto com
  Lucas, incluindo execução e inspeção das simulações no GHDL e GTKWave.
- **Software:** criação de `adder_unsigned.vhd` e desenvolvimento compartilhado
  de `top_fp_adder.vhd` com Lucas; criação do Makefile de automação dos
  testbenches; e desenvolvimento dos scripts de `encode/decode` e dos testes
  automáticos das conversões.
- **Validation:** verificação do VHDL original e comparação das saídas com os
  resultados calculados manualmente, incluindo a validação das adaptações
  realizadas com Lucas.
- **Visualization:** seleção e interpretação dos sinais apresentados nas formas
  de onda, especialmente `sum`, `leado`, `sum_norm`, `expn` e `fracn`.

### Lucas Marques de Oliveira — Interface da DE10-Lite e Ambiente Quartus

- **Methodology:** definição da estratégia de adaptação do circuito original
  para uma interface empacotada e para os recursos da DE10-Lite.
- **Software:** desenvolvimento de `top_fp_adder.vhd` em conjunto com Guilherme,
  incluindo a interface de switches, botões, LEDs e displays, além da
  configuração dos arquivos do projeto Quartus.
- **Resources:** instalação, preparação e configuração do Quartus e dos recursos
  necessários para trabalhar com a placa DE10-Lite.
- **Investigation:** investigação do funcionamento do circuito em conjunto com
  Guilherme e identificação de incompatibilidades entre a arquitetura original
  e a placa atual.
- **Validation:** participação nos testbenches da interface adaptada e na
  conferência da configuração do projeto para a MAX 10.

### Marconde Correia Pinho — Documentação e Auditoria da IA

- **Data curation:** organização do repositório, das formas de onda, relatórios,
  capturas e fotografias necessárias para reproduzir e auditar o projeto.
- **Writing – original draft:** elaboração inicial do tutorial e do relatório
  no README.
- **Writing – review & editing:** revisão e integração da documentação técnica,
  incluindo o diário de IA e as correções feitas durante o projeto.

## Matriz consolidada

| Papel CRediT | Guilherme | Lucas | Marconde |
|---|:---:|:---:|:---:|
| Conceptualization | ✓ |  |  |
| Methodology | ✓ | ✓ |  |
| Formal analysis | ✓ |  |  |
| Investigation | ✓ | ✓ |  |
| Software | ✓ | ✓ |  |
| Validation | ✓ | ✓ |  |
| Resources |  | ✓ |  |
| Data curation |  |  | ✓ |
| Visualization | ✓ |  |  |
| Writing – original draft |  |  | ✓ |
| Writing – review & editing |  |  | ✓ |

Os papéis **Funding acquisition**, **Project administration** e
**Supervision** não foram atribuídos, pois as atividades informadas não
indicam captação de financiamento, responsabilidade geral pela coordenação do
projeto ou supervisão externa exercida por um integrante do grupo.

## Declaração para o relatório

> **Guilherme Rocha Muzi Franco:** Conceptualization, Methodology, Formal
> analysis, Investigation, Software, Validation e Visualization.
> **Lucas Marques de Oliveira:** Methodology, Software, Resources, Investigation e
> Validation.
> **Marconde Correia Pinho:** Data curation, Writing – original
> draft e Writing – review & editing.

Todos os integrantes são responsáveis pela revisão técnica da entrega final,
mas os papéis acima registram as responsabilidades específicas informadas pelo
grupo.

## Automação e conversores — Guilherme Rocha Muzi Franco

Guilherme também criou os scripts para automatizar a execução dos testbenches
e o armazenamento das formas de onda. Além disso, desenvolveu o conversor
`scripts/fp13.py`:

- `encode`: transforma um número decimal normalizado nos campos `sign`,
  `exponent` e `fraction` que devem ser inseridos na placa;
- `decode`: interpreta diretamente a palavra hexadecimal `00SEFF`
  apresentada pelos seis displays, confere `LEDR9` e considera `LEDR8` para
  distinguir resultado válido de underflow/overflow;
- `scripts/test_fp13.py`: verifica automaticamente conversões exatas,
  truncamento, limites e valores fora da faixa.

Essas funções foram integradas ao Makefile pelos alvos `make encode`,
`make decode` e `make converter-test`.
