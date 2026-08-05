GHDL ?= ghdl
PYTHON ?= python3
VHDL_STD ?= 08

INPUT ?= 0
DISPLAY ?=
LEDR8 ?=

BUILD_DIR := build/ghdl
WAVE_DIR := build/waves

GHDL_FLAGS := --std=$(VHDL_STD) --workdir=$(BUILD_DIR)
RUN_FLAGS := --assert-level=error --ieee-asserts=disable-at-0

.DEFAULT_GOAL := all

.PHONY: all original normalization packed board board-svg regression
.PHONY: encode decode converter-test help prepare clean

# Run the four testbenches used in the report.
all: original normalization packed board

help:
	@echo "Uso:"
	@echo "  make                Executa os quatro testbenches principais"
	@echo "  make original       Testa o VHDL original do livro"
	@echo "  make normalization  Testa os quatro casos do 4o estagio"
	@echo "  make packed         Testa a interface empacotada de 13 bits"
	@echo "  make board          Testa a interface da DE10-Lite"
	@echo "  make board-svg      Gera dois SVGs: configuracao e resultados da placa"
	@echo "  make regression     Compara somador vetorial e original (sem onda, pois e exaustivo)"
	@echo "  make encode INPUT=13.25"
	@echo "  make decode DISPLAY=001499 LEDR8=1"
	@echo "  make converter-test Testa encode/decode"
	@echo "  make clean          Remove build/"
	@echo ""
	@echo "Formas de onda: $(WAVE_DIR)/*.vcd e $(WAVE_DIR)/*.ghw"

prepare:
	@mkdir -p $(BUILD_DIR) $(WAVE_DIR)

original: prepare
	@echo "[GHDL] utils/adder_testbench.vhd"
	@$(GHDL) -a $(GHDL_FLAGS) utils/adder.vhd
	@$(GHDL) -a $(GHDL_FLAGS) utils/adder_testbench.vhd
	@$(GHDL) -e $(GHDL_FLAGS) -o $(BUILD_DIR)/adder_testbench adder_testbench
	@$(BUILD_DIR)/adder_testbench $(RUN_FLAGS) \
		--vcd=$(WAVE_DIR)/adder.vcd \
		--wave=$(WAVE_DIR)/adder.ghw

normalization: prepare
	@echo "[GHDL] utils/normalization_testbench.vhd"
	@$(GHDL) -a $(GHDL_FLAGS) utils/adder.vhd
	@$(GHDL) -a $(GHDL_FLAGS) utils/normalization_testbench.vhd
	@$(GHDL) -e $(GHDL_FLAGS) -o $(BUILD_DIR)/normalization_testbench normalization_testbench
	@$(BUILD_DIR)/normalization_testbench $(RUN_FLAGS) \
		--vcd=$(WAVE_DIR)/normalization.vcd \
		--wave=$(WAVE_DIR)/normalization.ghw

packed: prepare
	@echo "[GHDL] adder_unsigned_testbench.vhd"
	@$(GHDL) -a $(GHDL_FLAGS) adder_unsigned.vhd
	@$(GHDL) -a $(GHDL_FLAGS) adder_unsigned_testbench.vhd
	@$(GHDL) -e $(GHDL_FLAGS) -o $(BUILD_DIR)/adder_unsigned_testbench adder_unsigned_testbench
	@$(BUILD_DIR)/adder_unsigned_testbench $(RUN_FLAGS) \
		--vcd=$(WAVE_DIR)/adder_unsigned.vcd \
		--wave=$(WAVE_DIR)/adder_unsigned.ghw

board: prepare
	@echo "[GHDL] top_fp_adder_testbench.vhd"
	@$(GHDL) -a $(GHDL_FLAGS) adder_unsigned.vhd
	@$(GHDL) -a $(GHDL_FLAGS) hex_to_sseg.vhd top_fp_adder.vhd
	@$(GHDL) -a $(GHDL_FLAGS) top_fp_adder_testbench.vhd
	@$(GHDL) -e $(GHDL_FLAGS) -o $(BUILD_DIR)/top_fp_adder_testbench top_fp_adder_testbench
	@$(BUILD_DIR)/top_fp_adder_testbench $(RUN_FLAGS) \
		--vcd=$(WAVE_DIR)/top_fp_adder.vcd \
		--wave=$(WAVE_DIR)/top_fp_adder.ghw

board-svg: board
	@echo "[SVG] Generating board input and result evidence..."
	@$(PYTHON) scripts/vcd_to_board_svg.py \
		$(WAVE_DIR)/top_fp_adder.vcd \
		docs/images/board-input-sequence.svg \
		docs/images/board-result-cases.svg

regression: prepare
	@echo "[GHDL] adder_unsigned_regression_testbench.vhd"
	@$(GHDL) -a $(GHDL_FLAGS) utils/adder.vhd
	@$(GHDL) -a $(GHDL_FLAGS) adder_unsigned.vhd
	@$(GHDL) -a $(GHDL_FLAGS) adder_unsigned_regression_testbench.vhd
	@$(GHDL) -e $(GHDL_FLAGS) -o $(BUILD_DIR)/adder_unsigned_regression_testbench \
		adder_unsigned_regression_testbench
	@$(BUILD_DIR)/adder_unsigned_regression_testbench $(RUN_FLAGS)

clean:
	@$(GHDL) --clean --workdir=$(BUILD_DIR) 2>/dev/null || true
	@rm -rf build

encode:
	@$(PYTHON) scripts/fp13.py encode $(INPUT)

decode:
	@$(PYTHON) scripts/fp13.py decode $(DISPLAY) \
		$(if $(LEDR8),--ledr8 $(LEDR8))

converter-test:
	@$(PYTHON) scripts/test_fp13.py
