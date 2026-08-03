library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use std.env.all;

entity adder_unsigned_regression_testbench is
end entity adder_unsigned_regression_testbench;

architecture test of adder_unsigned_regression_testbench is
    signal a, b       : unsigned(12 downto 0) := (others => '0');
    signal packed_res : unsigned(12 downto 0);

    signal original_sign : std_logic;
    signal original_exp  : std_logic_vector(3 downto 0);
    signal original_frac : std_logic_vector(7 downto 0);

    function number(
        sign_bit : std_logic;
        fraction : natural;
        exponent : natural
    ) return unsigned is
        variable value : unsigned(12 downto 0);
    begin
        value(12)          := sign_bit;
        value(11 downto 8) := to_unsigned(exponent, 4);
        value(7 downto 0)  := to_unsigned(fraction, 8);
        return value;
    end function;

    type sample_array is array (natural range <>) of unsigned(12 downto 0);
    constant B_SAMPLES : sample_array := (
        number('0',   0,  0), number('1',   0,  0),
        number('0', 128,  0), number('1', 128,  0),
        number('0', 255,  0), number('1', 255,  0),
        number('0', 128,  1), number('1', 129,  6),
        number('0', 129,  7), number('1', 128,  8),
        number('0', 195,  8), number('1', 195,  8),
        number('0', 128, 14), number('1', 255, 14),
        number('0', 128, 15), number('1', 255, 15)
    );
begin
    original : entity work.fp_adder(arch)
        port map (
            sign1 => a(12),
            sign2 => b(12),
            exp1  => std_logic_vector(a(11 downto 8)),
            exp2  => std_logic_vector(b(11 downto 8)),
            frac1 => std_logic_vector(a(7 downto 0)),
            frac2 => std_logic_vector(b(7 downto 0)),
            sign_out => original_sign,
            exp_out  => original_exp,
            frac_out => original_frac
        );

    packed : entity work.adder_unsigned(arch)
        port map (
            a => a, b => b, res => packed_res,
            underflow => open,
            overflow => open
        );

    stimulus : process
        variable expected : unsigned(12 downto 0);
        variable count    : natural := 0;
    begin
        -- Compare every possible 13-bit A word against 16 representative B
        -- words. This is an equivalence test: the packed adaptation must match
        -- the original book entity bit for bit, including boundary behaviors.
        for raw_a in 0 to 8191 loop
            for sample_index in B_SAMPLES'range loop
                a <= to_unsigned(raw_a, 13);
                b <= B_SAMPLES(sample_index);
                wait for 1 ns;

                expected := unsigned(original_sign & original_exp & original_frac);
                assert packed_res = expected
                    report "Packed adaptation mismatch: A=0x" &
                           to_hstring(to_unsigned(raw_a, 13)) &
                           ", B=0x" & to_hstring(B_SAMPLES(sample_index)) &
                           ", packed=0x" & to_hstring(packed_res) &
                           ", original=0x" & to_hstring(expected)
                    severity failure;
                count := count + 1;
            end loop;
        end loop;

        report "Equivalence regression completed: all " &
               integer'image(count) & " combinations matched the book core."
            severity note;
        finish;
    end process stimulus;
end architecture test;
