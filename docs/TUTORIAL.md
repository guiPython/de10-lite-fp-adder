# Tutorial reproduzível

Este é o roteiro completo: simular, compilar no Quartus, gravar a FPGA e
interpretar o resultado.

## 1. Pré-requisitos

Para simulação:

- GHDL com VHDL-2008;
- GTKWave;
- GNU Make;
- Python 3.

Para a placa:

- Intel Quartus com suporte à família **MAX 10**;
- driver USB-Blaster;
- DE10-Lite e cabo USB.

Arquivos usados pelo Quartus:

| Arquivo | Função |
|---|---|
| `top_fp_adder.qpf` | abre o projeto |
| `top_fp_adder.qsf` | dispositivo, fontes e pinos |
| `top_fp_adder.sdc` | restrição do clock de 50 MHz |
| `adder_unsigned.vhd` | somador de 13 bits |
| `hex_to_sseg.vhd` | decodificador de sete segmentos |
| `top_fp_adder.vhd` | entidade de topo da DE10-Lite |

Na distribuição pronta, os seis arquivos ficam no mesmo nível:

```text
de10-lite-fp-adder/          ← esta já é a pasta do projeto Quartus
├── top_fp_adder.qpf         ← abrir este arquivo
├── top_fp_adder.qsf
├── top_fp_adder.sdc
├── adder_unsigned.vhd
├── hex_to_sseg.vhd
└── top_fp_adder.vhd
```

Não mova esses arquivos ao usar o projeto pronto. `baseline/`, `utils/`,
testbenches, `scripts/`, `docs/` e `Makefile` são importantes para validação e
documentação, mas não entram na síntese do topo.

## 2. Validar antes da síntese

Na raiz do repositório:

```bash
make
make regression
make converter-test
make board-svg
```

Resultados esperados:

- 7 casos do núcleo original;
- 4 casos obrigatórios de normalização;
- 11 casos do somador vetorial;
- interface da placa aprovada;
- 131072 comparações equivalentes;
- 10 testes do conversor.

Abra a onda principal:

```bash
gtkwave build/waves/normalization.vcd
```

Observe `sum`, `leado`, `sum_norm`, `expn`, `fracn` e `case_index`. A análise
dos quatro intervalos está em [VALIDACAO_SIMULACAO.md](VALIDACAO_SIMULACAO.md).

## 3. Abrir ou criar o projeto?

### Opção recomendada — abrir o projeto existente

Ao clonar ou baixar este repositório, **não use New Project Wizard**. A raiz já
é a pasta do projeto e o QSF já contém dispositivo, fontes, padrões elétricos e
pinout.

1. Inicie o Quartus.
2. Use **File → Open Project**.
3. Selecione `top_fp_adder.qpf` na raiz do repositório.
4. Se a versão instalada solicitar atualização, aceite mantendo uma cópia do
   repositório.

Se quiser uma pasta independente apenas para o Quartus, crie, por exemplo,
`top_fp_adder_quartus/`, copie para ela os **seis arquivos** da árvore acima e
abra o `.qpf` copiado. Não altere os nomes nem separe os VHDL do QSF, pois os
caminhos são relativos.

### Alternativa — criar do zero

Use esta opção somente se o `.qpf` não puder ser aberto ou se o professor
exigir a criação manual.

1. Crie uma pasta vazia, por exemplo `top_fp_adder_novo/`.
2. Copie para essa pasta apenas:

   ```text
   adder_unsigned.vhd
   hex_to_sseg.vhd
   top_fp_adder.vhd
   top_fp_adder.sdc
   ```

3. Mantenha o `top_fp_adder.qsf` original fora dessa pasta para importá-lo
   depois. O Quartus não importa um QSF sobre ele mesmo.
4. Abra **File → New Project Wizard** e preencha:
   - Working directory: a pasta nova;
   - Project name: `top_fp_adder`;
   - Top-level entity: `top_fp_adder`.
5. Em **Add Files**, adicione os três VHDL e o SDC copiados.
6. Em **Family & Device Settings**, escolha `MAX 10` e
   `10M50DAF484C7G`.
7. Finalize o assistente.
8. Abra **Assignments → Import Assignments**, selecione o
   `top_fp_adder.qsf` do repositório original e importe as atribuições que
   ainda não existem. Isso recupera o pinout e os padrões elétricos.
9. Salve o projeto e confira Device, Files e Pin Planner conforme a lista
   abaixo.

Criar do zero não melhora o circuito; apenas recria arquivos `.qpf/.qsf` que o
repositório já fornece.

### Conferência obrigatória nas duas opções

Confirme a configuração:

1. Em **Assignments → Settings → General**, verifique
   **Top-level entity = `top_fp_adder`**.
2. Em **Assignments → Device**, verifique:
   - Family: `MAX 10`;
   - Device: `10M50DAF484C7G`.
3. Em **Assignments → Settings → Files**, confirme:
   - `adder_unsigned.vhd`;
   - `hex_to_sseg.vhd`;
   - `top_fp_adder.vhd`;
   - `top_fp_adder.sdc`.
4. Em **Assignments → Pin Planner**, confira se `clk`, `bt_clear`, `bt_adv`,
   `sw[9..0]`, `ledr[9..0]` e `hex0..hex5` possuem pinos.

Esses dados vêm automaticamente de `top_fp_adder.qsf`; não os redigite se já
estiverem carregados.

Se `10M50DAF484C7G` não estiver disponível, feche o projeto e instale o pacote
de dispositivos **Intel Quartus Prime MAX 10 FPGA**. Escolher outro dispositivo
torna o pinout inválido.

## 4. Compilar

1. Selecione **Processing → Start Compilation**.
2. Aguarde todas as etapas: Analysis & Synthesis, Fitter, Assembler e Timing
   Analyzer.
3. O resultado deve ser **Full Compilation was successful**.
4. Confirme que foi criado:

```text
output_files/top_fp_adder.sof
```

Registre no **Compilation Report**:

- **Flow Summary:** compilação concluída e dispositivo correto;
- **Fitter → Resource Section:** utilização de lógica e registradores;
- **TimeQuest Timing Analyzer:** clock `clk` de 50 MHz, período de 20 ns;
- **Assembler:** geração do `.sof`.

Warnings devem ser lidos e explicados; não considere “sem errors” suficiente
sem conferir dispositivo, pinos e timing.

Compilação equivalente pelo terminal do Quartus:

```bash
quartus_sh --flow compile top_fp_adder
```

Execute o comando na raiz do projeto e em um terminal no qual as ferramentas
do Quartus estejam no `PATH`.

## 5. Conectar e programar a DE10-Lite

1. Conecte o cabo à porta USB-Blaster da DE10-Lite e ligue a placa.
2. Abra **Tools → Programmer**.
3. Clique em **Hardware Setup** e selecione `USB-Blaster [USB-0]` ou o nome
   equivalente disponível.
4. Mantenha **Mode = JTAG**.
5. Se a cadeia estiver vazia, clique em **Auto Detect** e confirme o MAX 10.
6. Clique em **Add File** e escolha
   `output_files/top_fp_adder.sof`.
7. Marque **Program/Configure** na linha do arquivo.
8. Clique em **Start**.
9. Só prossiga quando o progresso indicar **100% (Successful)**.

Se o USB-Blaster não aparecer, instale o driver presente na instalação do
Quartus, reconecte o cabo e reabra **Hardware Setup**.

Programação equivalente pelo terminal:

```bash
jtagconfig
quartus_pgm -m jtag -o "p;output_files/top_fp_adder.sof"
```

O `.sof` configura a SRAM da FPGA e é volátil: após desligar a placa, repita a
programação.

## 6. Inserir os operandos

`KEY1` confirma; `KEY0` volta uma etapa. Os botões são ativos em zero.

| Estado | Chaves usadas | Valor mostrado |
|---|---|---|
| `S1` | `SW9` | sinal de A: `0/1` |
| `F1` | `SW9..SW2` | fração de A: `000..255` |
| `E1` | `SW9..SW6` | expoente de A: `00..15` |
| `S2` | `SW9` | sinal de B: `0/1` |
| `F2` | `SW9..SW2` | fração de B: `000..255` |
| `E2` | `SW9..SW6` | expoente de B: `00..15` |

Em cada etapa:

1. posicione as chaves;
2. confira o decimal nos displays;
3. confira os mesmos bits nos LEDs;
4. pressione e solte `KEY1`.

Depois de `E2`, leia:

```text
HEX5..HEX0 = 00SEFF
LEDR9      = sinal
LEDR8      = 1 válido; 0 underflow/overflow
```

Para converter a saída:

```bash
make decode DISPLAY=001499 LEDR8=1
```

Pressionar `KEY1` no resultado inicia uma nova operação.

## 7. Teste físico mínimo

| Caso | A `(S,E,F)` | B `(S,E,F)` | Saída esperada | Validade |
|---:|---|---|---|---:|
| 1 | `(0,3,138)` | `(1,4,222)` | `001499` | 1 |
| 2 | `(1,3,144)` | `(0,3,128)` | `001080` | 1 |
| 3 | `(1,0,129)` | `(0,0,128)` | `001000` | 0 |
| 4 | `(0,3,144)` | `(0,3,128)` | `000488` | 1 |
| 5 | `(0,15,255)` | `(0,15,255)` | `0000FF` | 0 |

Fotografe pelo menos uma entrada e o resultado de cada caso. Registre também
compilação, Pin Planner, recursos, timing e Programmer em 100%. Os nomes
sugeridos estão em [evidence/README.md](evidence/README.md).

## 8. Diagnóstico rápido

| Problema | Verificação |
|---|---|
| dispositivo não aparece | instale o pacote MAX 10 |
| entidade não encontrada | confira os três VHDL em Settings → Files |
| pinos vazios | abra o `.qpf` correto e confira o `.qsf` |
| `.sof` não existe | a compilação não chegou ao Assembler |
| USB-Blaster não aparece | driver, cabo, alimentação e Hardware Setup |
| programação falha | modo JTAG, dispositivo detectado e `.sof` atual |
| botão avança mais de uma vez | pressione e solte; confira clock e sincronizador |
| display invertido | os segmentos são ativos em zero |
| decimal 256 vezes maior | use `(F/256)×2^E`, não `F×2^E` |
| `LEDR8=0` no resultado | ocorreu underflow ou overflow |

## Referências do Quartus

- [Criação de projeto pelo New Project Wizard](https://www.intel.com/content/www/us/en/docs/programmable/683133/22-2-19-3-0/creating-a-new-project.html)
- [Importação de atribuições de pinos entre projetos](https://www.intel.com/content/www/us/en/docs/programmable/683143/21-3/importing-and-exporting-i-o-pin-assignments.html)
- [Janela Programmer e Hardware Setup](https://www.intel.com/content/www/us/en/programmable/quartushelp/17.0/program/pgm/pgm_image.htm)
