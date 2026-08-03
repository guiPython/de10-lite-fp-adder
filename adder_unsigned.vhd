library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity adder_unsigned is
    port (
        -- Packed 13-bit book format: [sign(1) | exponent(4) | fraction(8)].
        -- Numeric value: (-1)^sign * 0.fraction * 2^exponent.
        a, b : in  unsigned(12 downto 0);
        res  : out unsigned(12 downto 0)
    );
end entity adder_unsigned;

architecture arch of adder_unsigned is
    signal result_sign : std_logic;
    signal result_exp  : std_logic_vector(3 downto 0);
    signal result_frac : std_logic_vector(7 downto 0);
begin
    -- [ADAPTATION 1/2] Replace the original nine separate input/output ports
    -- with two packed input words and one packed output word. No arithmetic is
    -- performed in this wrapper.
    -- This wrapper changes only the port organization. The mathematical core
    -- is the original fp_adder from Listing 3.19: sort, align, add/subtract
    -- with a 9-bit intermediate, and normalize back to the 13-bit format.
    book_adder : entity work.fp_adder(arch)
        port map (
            sign1 => a(12),
            sign2 => b(12),
            exp1  => std_logic_vector(a(11 downto 8)),
            exp2  => std_logic_vector(b(11 downto 8)),
            frac1 => std_logic_vector(a(7 downto 0)),
            frac2 => std_logic_vector(b(7 downto 0)),
            sign_out => result_sign,
            exp_out  => result_exp,
            frac_out => result_frac
        );

    -- [ADAPTATION 2/2] Repack the three original output ports without changing
    -- any bit. The external result therefore remains exactly 13 bits wide.
    res <= unsigned(result_sign & result_exp & result_frac);
end architecture arch;
