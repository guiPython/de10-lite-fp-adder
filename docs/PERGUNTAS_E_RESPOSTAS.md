# Perguntas e respostas

## 1. A entrada e a saída têm 13 bits?

Sim. Cada palavra é `[S(1)|E(4)|F(8)]`. O somador recebe `a` e `b` e devolve
`res`, todos com 13 bits.

## 2. Por que existe uma soma de 9 bits?

Duas frações de 8 bits podem gerar carry. `sum(8)` é temporário; depois da
normalização a fração volta a 8 bits. A solução de 25 bits foi removida porque
não reproduzia o algoritmo do livro.

## 3. Qual é a fórmula correta?

```text
value = (-1)^S × (F/256) × 2^E
```

O sinal usa módulo: `0` positivo e `1` negativo. Não é complemento de dois.

## 4. `50000` pode ser representado?

Não. Entradas não nulas normalizadas usam `128≤F≤255` e `0≤E≤15`; a faixa em
módulo é `0.5..32640`.

## 5. Quais são os quatro estágios?

`sort → align → add/sub → normalize`. O último estágio conta zeros, desloca a
fração e ajusta o expoente ou trata carry/underflow.

## 6. A contagem de zeros funciona?

Sim para resultados não nulos: `leado=0..7` indica a posição do primeiro `1`.
Os quatro casos obrigatórios passaram. O Listing possui uma limitação:
`leado=7` também é usado quando `sum=0`, então cancelamento exato com expoente
alto pode manter expoente não zero.

## 7. Como underflow e overflow são tratados?

- underflow: um resultado não nulo exigiria expoente negativo;
- overflow: um carry com `E=15` exigiria expoente 16.

O resultado literal de 13 bits é preservado, mas `LEDR8` apaga para indicar
que a palavra exibida não representa a soma exata. Cancelamento exato mantém
`LEDR8` aceso.

## 8. A interface vetorial mudou a matemática?

Não. `adder_unsigned.vhd` repete os quatro estágios. Uma regressão comparou
seu `res` com `utils/adder.vhd` em 131072 combinações e não encontrou
divergências. As flags apenas informam faixa.

## 9. Como inserir os operandos?

`KEY1` confirma e `KEY0` retorna:

```text
S1: SW9       sinal A
F1: SW9..SW2  fração A
E1: SW9..SW6  expoente A
S2/F2/E2:     mesmos campos de B
```

O decimal aparece nos displays e os bits usados são espelhados nos LEDs.

## 10. Como ler o resultado?

```text
HEX5..HEX0 = 00SEFF
LEDR9 = S
LEDR8 = resultado válido
```

Exemplo: `001499` significa `S=1`, `E=4`, `F=0x99=153`, portanto
`−(153/256)×2^4=−9.5625`.

## 11. Quais comandos validam o projeto?

```bash
make
make regression
make converter-test
make board-svg
```

As ondas ficam em `build/waves/`. Para abrir o quarto estágio:

```bash
gtkwave build/waves/normalization.vcd
```

## 12. Como converter a saída física?

```bash
make decode DISPLAY=001499 LEDR8=1
```

Sem `LEDR8`, o script informa que a validade é desconhecida.

## 13. Como levar o projeto ao Quartus?

Não crie outro projeto: abra `top_fp_adder.qpf` na raiz. Mantenha na mesma
pasta `.qpf`, `.qsf`, `.sdc`, `adder_unsigned.vhd`, `hex_to_sseg.vhd` e
`top_fp_adder.vhd`. O QSF já define dispositivo, fontes e pinos.

Se for necessário criar manualmente, coloque os três VHDL e o SDC em uma pasta
nova, use o New Project Wizard e importe o QSF original em **Assignments →
Import Assignments**. Depois confira Device, Files e Pin Planner e execute
**Processing → Start Compilation**. A saída esperada é
`output_files/top_fp_adder.sof`.

## 14. Como executar na DE10-Lite?

Conecte e ligue a placa, abra **Tools → Programmer**, selecione USB-Blaster em
Hardware Setup, use modo JTAG, adicione o `.sof`, marque Program/Configure e
clique em Start. Depois de `100% (Successful)`, insira os seis campos pelas
chaves. O roteiro completo está em [TUTORIAL.md](TUTORIAL.md).

## 15. O projeto já está fisicamente validado?

O GHDL, a regressão, o conversor e a conferência de sintetizabilidade passaram.
A validação física só estará completa após registrar compilação/timing no
Quartus, programação do `.sof` e os cinco casos na placa.

## 16. O warning sobre comparação não numérica invalida o circuito?

Não por si só. O Listing compara `exp & frac` como vetores de igual largura; a
ordem lexicográfica coincide com a ordem binária sem sinal. O warning foi
mantido para preservar o original, mas os relatórios do Quartus ainda devem
ser revisados.

## 17. Como a IA foi usada?

O Codex apoiou revisão, testes, interface, automação e documentação. A hipótese
incorreta `F×2^E` foi rejeitada após confronto com o livro. Decisões e
evidências estão em [AI_AUDIT.md](AI_AUDIT.md).

## 18. O que falta para a entrega?

Captura interpretada do GTKWave, relatórios do Quartus, Programmer em 100%,
fotos dos testes físicos, reflexões individuais sobre IA e revisão final dos
links. Veja [RUBRICA_CHECKLIST.md](RUBRICA_CHECKLIST.md).
