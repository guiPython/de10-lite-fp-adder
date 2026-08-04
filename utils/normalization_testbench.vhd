library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use std.env.all;

entity normalization_testbench is
end entity normalization_testbench;

architecture test of normalization_testbench is
    signal sign1, sign2 : std_logic := '0';
    signal exp1, exp2   : std_logic_vector(3 downto 0) := (others => '0');
    signal frac1, frac2 : std_logic_vector(7 downto 0) := (others => '0');
    signal sign_out     : std_logic;
    signal exp_out      : std_logic_vector(3 downto 0);
    signal frac_out     : std_logic_vector(7 downto 0);
    signal case_index   : natural := 0;
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
        procedure run_case(
            constant index_value   : natural;
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
            case_index <= index_value;
            sign1 <= input_sign1;
            frac1 <= std_logic_vector(to_unsigned(input_frac1, 8));
            exp1  <= std_logic_vector(to_unsigned(input_exp1, 4));
            sign2 <= input_sign2;
            frac2 <= std_logic_vector(to_unsigned(input_frac2, 8));
            exp2  <= std_logic_vector(to_unsigned(input_exp2, 4));

            -- Ten nanoseconds are reserved for settling and ten more keep the
            -- stable result visible as a wide interval in GTKWave/Questa.
            wait for 10 ns;
            assert sign_out = expected_sign and
                   unsigned(frac_out) = expected_frac and
                   unsigned(exp_out) = expected_exp
                report "Normalization case " & integer'image(index_value) &
                       " failed: actual=[" & std_logic'image(sign_out) &
                       "|" & to_hstring(exp_out) &
                       "|" & to_hstring(frac_out) & "]"
                severity failure;
            wait for 10 ns;
        end procedure;
    begin
        -- Case 1 - sort, align and subtract; the result is already normalized.
        -- +0.10001010 * 2^3 - 0.11011110 * 2^4
        -- = -0.10011001 * 2^4. leado=0.
        run_case(1, '0', 138, 3, '1', 222, 4, '1', 153, 4);

        -- Case 2 - subtraction creates three leading zeros. sum=000010000,
        -- leado=3 and sum_norm=10000000, so exponent changes from 3 to 0.
        run_case(2, '1', 144, 3, '0', 128, 3, '1', 128, 0);

        -- Case 3 - seven leading zeros would require exponent -7. Since the
        -- exponent is unsigned and starts at zero, the magnitude underflows.
        run_case(3, '1', 129, 0, '0', 128, 0, '1', 0, 0);

        -- Case 4 - addition produces carry sum(8)=1. The fraction shifts right
        -- once from 100010000 to 10001000 and exponent increments from 3 to 4.
        run_case(4, '0', 144, 3, '0', 128, 3, '0', 136, 4);

        report "All four required normalization cases passed."
            severity note;
        finish;
    end process stimulus;
end architecture test;
