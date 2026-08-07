# Checklist da rubrica

## Evidências por critério

| Critério | Evidência pronta | Pendente |
|---|---|---|
| Interpretação | fórmula, exemplos, `encode/decode`, limites e `00SEFF` | cada integrante fazer a conversão nos dois sentidos sem script |
| Hardware | diagramas, FSM, justificativas, QSF, pinout e testbench | compilar no Quartus e fotografar a placa |
| Simulação | quatro casos com `assert`, SVG do VCD e regressão de 131072 pares | captura legível do GTKWave com legenda |
| IA e gestão | objetivos, erro, correção, decisões e CRediT | reflexões individuais e conversa integral, se exigida |
| Reprodutibilidade | README, tutorial, Makefile e conversores | testar o roteiro em outra máquina |

## Antes da entrega

- [ ] Manter `.qpf`, `.qsf`, `.sdc` e os três VHDL na mesma pasta.
- [ ] Abrir o projeto existente; criar outro somente se for necessário.
- [ ] Abrir `top_fp_adder.qpf` e confirmar `10M50DAF484C7G`.
- [ ] Conferir pinos no Pin Planner.
- [ ] Executar **Start Compilation** sem erros.
- [ ] Registrar recursos e timing do clock de 50 MHz.
- [ ] Confirmar `output_files/top_fp_adder.sof`.
- [ ] Programar pelo USB-Blaster e registrar `100% (Successful)`.
- [ ] Executar na placa os quatro casos obrigatórios e o overflow.
- [ ] Fotografar entrada, displays e LEDs de cada caso.
- [ ] Decodificar cada `00SEFF` para decimal.
- [ ] Inserir captura GTKWave de `0–80 ns` com `sum`, `leado`, `sum_norm`,
  `expn` e `fracn`.
- [ ] Adicionar reflexão de IA de cada integrante.
- [ ] Conferir links e imagens no GitHub.
- [ ] Enviar o link privado correto no Moodle.

O projeto só deve ser declarado fisicamente validado depois da compilação,
programação e execução real dos casos na DE10-Lite.
