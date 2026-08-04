# Oscilador MAX10_CLK1_50 da DE10-Lite: 50 MHz, periodo de 20 ns.
create_clock -name clk -period 20.000 [get_ports {clk}]
derive_clock_uncertainty
