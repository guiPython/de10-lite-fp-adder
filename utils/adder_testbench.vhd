library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use std.env.all;

entity adder_testbench is
end entity adder_testbench;

architecture test of adder_testbench is
    signal sign1, sign2 : std_logic := '0';
    signal exp1, exp2   : std_logic_vector(3 downto 0) := (others => '0');
    signal frac1, frac2 : std_logic_vector(7 downto 0) := (others => '0');
    signal sign_out     : std_logic;
    signal exp_out      : std_logic_vector(3 downto 0);
    signal frac_out     : std_logic_vector(7 downto 0);
    signal test_index   : natural := 0;
begin
    uut : entity work.fp_adder(arch)
        port map (
            sign1 => sign1, sign2 => sign2,
            exp1 => exp1, exp2 => exp2,
            frac1 => frac1, frac2 => frac2,
            sign_out => sign_out,
            exp_out => exp_out,
            frac_out => frac_out
        );

    stimulus : process
        variable tests_run : natural := 0;

        procedure check(
            constant description   : string;
            constant input_sign1   : std_logic;
            constant input_frac1   : natural;
            constant input_exp1    : natural;
            constant input_sign2   : std_logic;
            constant input_frac2   : natural;
            constant input_exp2    : natural;
            constant expected_sign : std_logic;
            constant expected_frac : natural;
            constant expected_exp  : natural
        ) is
        begin
            sign1 <= input_sign1;
            frac1 <= std_logic_vector(to_unsigned(input_frac1, 8));
            exp1  <= std_logic_vector(to_unsigned(input_exp1, 4));
            sign2 <= input_sign2;
            frac2 <= std_logic_vector(to_unsigned(input_frac2, 8));
            exp2  <= std_logic_vector(to_unsigned(input_exp2, 4));
            test_index <= tests_run + 1;
            wait for 1 ns;

            assert sign_out = expected_sign and
                   unsigned(frac_out) = expected_frac and
                   unsigned(exp_out) = expected_exp
                report description &
                       ": actual=[" & std_logic'image(sign_out) &
                       "|" & to_hstring(exp_out) &
                       "|" & to_hstring(frac_out) & "]"
                severity failure;

            tests_run := tests_run + 1;
        end procedure;
    begin
        -- Book example 1: sort, align and subtract.
        -- +0.10001010 * 2^3 - 0.11011110 * 2^4
        -- = -0.10011001 * 2^4.
        check("book example 1", '0', 138, 3, '1', 222, 4, '1', 153, 4);

        -- Book example 2: subtraction creates three leading zeros.
        -- -0.10010000 * 2^3 + 0.10000000 * 2^3
        -- = -0.00010000 * 2^3 = -0.10000000 * 2^0.
        check("book example 2", '1', 144, 3, '0', 128, 3, '1', 128, 0);

        -- Book example 3: seven left shifts would require exponent -7.
        -- The result is therefore flushed to zero at exponent zero.
        check("book example 3 underflow", '1', 129, 0, '0', 128, 0,
              '1', 0, 0);

        -- Book example 4: the ninth sum bit is a carry-out. Shift right once
        -- and increment the exponent: 272 * 2^3 -> 136 * 2^4.
        check("book example 4 carry", '0', 144, 3, '0', 128, 3,
              '0', 136, 4);

        -- Boundary check for the leading-zero counter. A difference of one at
        -- exponent seven requires exactly seven left shifts and is normalized.
        check("seven leading zeros", '0', 129, 7, '1', 128, 7,
              '0', 128, 0);

        -- Literal Listing 3.19 behavior for exact cancellation at exponent 8.
        -- leado cannot distinguish sum=0 from sum=1, so the code emits a zero
        -- fraction with exponent 1 instead of the all-zero representation.
        check("literal zero-normalization behavior", '0', 128, 8,
              '1', 128, 8, '1', 0, 1);

        -- Literal Listing 3.19 behavior when a carry tries to increment the
        -- maximum 4-bit exponent. No overflow flag exists, so 15 + 1 wraps to 0.
        check("literal exponent-overflow behavior", '0', 255, 15,
              '0', 255, 15, '0', 255, 0);

        report "Original book implementation: all " &
               integer'image(tests_run) & " observed behaviors passed."
            severity note;
        finish;
    end process stimulus;
end architecture test;
