library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use std.env.all;

entity top_fp_adder_testbench is
end entity top_fp_adder_testbench;

architecture test of top_fp_adder_testbench is
    -- Board-level inputs and outputs exposed by top_fp_adder.
    signal clk      : std_logic := '0';
    signal bt_clear : std_logic := '1';
    signal bt_adv   : std_logic := '1';
    signal sw       : std_logic_vector(9 downto 0) := (others => '0');
    signal ledr     : std_logic_vector(9 downto 0);
    signal hex0, hex1, hex2, hex3, hex4, hex5 : std_logic_vector(7 downto 0);

    -- Independent seven-segment lookup used to check the physical active-low
    -- output pattern. The returned order is [dp g f e d c b a].
    function segments(
        hex : std_logic_vector(3 downto 0);
        dp  : std_logic := '1'
    ) return std_logic_vector is
        variable result_value : std_logic_vector(7 downto 0);
    begin
        result_value(7) := dp;
        case hex is
            when "0000" => result_value(6 downto 0) := "1000000";
            when "0001" => result_value(6 downto 0) := "1111001";
            when "0010" => result_value(6 downto 0) := "0100100";
            when "0011" => result_value(6 downto 0) := "0110000";
            when "0100" => result_value(6 downto 0) := "0011001";
            when "0101" => result_value(6 downto 0) := "0010010";
            when "0110" => result_value(6 downto 0) := "0000010";
            when "0111" => result_value(6 downto 0) := "1111000";
            when "1000" => result_value(6 downto 0) := "0000000";
            when "1001" => result_value(6 downto 0) := "0010000";
            when "1010" => result_value(6 downto 0) := "0001000";
            when "1011" => result_value(6 downto 0) := "0000011";
            when "1100" => result_value(6 downto 0) := "1000110";
            when "1101" => result_value(6 downto 0) := "0100001";
            when "1110" => result_value(6 downto 0) := "0000110";
            when others => result_value(6 downto 0) := "0001110";
        end case;
        return result_value;
    end function;
begin
    -- 50 MHz clock: 20 ns period, matching the DE10-Lite oscillator.
    clk <= not clk after 10 ns;

    uut : entity work.top_fp_adder(rtl)
        port map (
            clk => clk, bt_clear => bt_clear, bt_adv => bt_adv, sw => sw,
            ledr => ledr,
            hex0 => hex0, hex1 => hex1, hex2 => hex2,
            hex3 => hex3, hex4 => hex4, hex5 => hex5
        );

    stimulus : process
        -- Emulate one active-low KEY1 press. The 100 ns low/high intervals
        -- allow the three-stage synchronizer and edge detector to settle.
        procedure advance is
        begin
            bt_adv <= '0';
            wait for 100 ns;
            bt_adv <= '1';
            wait for 100 ns;
        end procedure;

        -- Emulate one active-low KEY0 press and verify the reverse transition.
        procedure go_back is
        begin
            bt_clear <= '0';
            wait for 100 ns;
            bt_clear <= '1';
            wait for 100 ns;
        end procedure;

        -- Enter one complete operand in the current S/F/E state sequence.
        -- Each step also verifies that LEDs mirror exactly the active switches:
        -- sign on LEDR9, significand on LEDR9..2 and exponent on LEDR9..6.
        procedure enter_number(
            constant sign_value        : std_logic;
            constant significand_value : natural;
            constant exponent_value    : natural
        ) is
        begin
            sw(9) <= sign_value;
            wait for 1 ns;
            assert ledr(9) = sign_value severity failure;
            assert ledr(8 downto 0) = "000000000" severity failure;
            advance;
            sw(9 downto 2) <= std_logic_vector(to_unsigned(significand_value, 8));
            wait for 1 ns;
            assert ledr(9 downto 2) = std_logic_vector(to_unsigned(significand_value, 8))
                severity failure;
            assert ledr(1 downto 0) = "00" severity failure;
            advance;
            sw(9 downto 6) <= std_logic_vector(to_unsigned(exponent_value, 4));
            wait for 1 ns;
            assert ledr(9 downto 6) = std_logic_vector(to_unsigned(exponent_value, 4))
                severity failure;
            assert ledr(5 downto 0) = "000000" severity failure;
            advance;
        end procedure;
    begin
        wait for 50 ns;

        -- Initial state: S1, sign of the first operand. Digit 5 is rendered
        -- as the closest available seven-segment representation of letter S.
        assert hex5 = segments("0101") severity failure;
        assert hex4 = segments("0001") severity failure;
        assert hex3 = x"FF" and hex2 = x"FF" and hex1 = x"FF"
            severity failure;

        -- KEY0 has no previous field at S1, so the initial state is retained.
        go_back;
        assert hex5 = segments("0101") and hex4 = segments("0001")
            report "KEY0 must retain S1 when no previous field exists"
            severity failure;

        -- Operand A = +0.11000011 * 2^8 (fraction field 195, exponent 8).
        -- S1: SW9=0 selects a positive operand and all other LEDs remain off.
        sw(9) <= '0';
        wait for 1 ns;
        assert ledr = "0000000000" severity failure;
        advance;

        -- Exercise one complete reverse transition: F1 -> S1 -> F1. This
        -- proves that the user can correct a field without restarting.
        go_back;
        assert hex5 = segments("0101") and hex4 = segments("0001")
            report "KEY0 must return from F1 to S1"
            severity failure;
        advance;

        -- F1: the first significand is entered on SW9..2. The displays show
        -- decimal 195 while LEDR9..2 show binary 11000011.
        assert hex5 = segments("1111") severity failure;
        assert hex4 = segments("0001") severity failure;
        assert hex3 = x"FF" severity failure;

        sw(9 downto 2) <= std_logic_vector(to_unsigned(195, 8));
        wait for 1 ns;
        assert hex2 = segments("0001") severity failure;
        assert hex1 = segments("1001") severity failure;
        assert hex0 = segments("0101") severity failure;
        assert ledr(9 downto 2) = std_logic_vector(to_unsigned(195, 8))
            severity failure;
        assert ledr(1 downto 0) = "00" severity failure;
        advance;

        -- E1: the first exponent is entered on SW9..6. The displays show
        -- decimal 08 while LEDR9..6 show binary 1000.
        assert hex5 = segments("1110") severity failure;
        assert hex4 = segments("0001") severity failure;
        assert hex3 = x"FF" and hex2 = x"FF" severity failure;

        sw(9 downto 6) <= std_logic_vector(to_unsigned(8, 4));
        wait for 1 ns;
        assert hex1 = segments("0000") severity failure;
        assert hex0 = segments("1000") severity failure;
        assert ledr(9 downto 6) = "1000" severity failure;
        assert ledr(5 downto 0) = "000000" severity failure;
        advance;

        -- S2: sign of the second operand.
        assert hex5 = segments("0101") severity failure;
        assert hex4 = segments("0010") severity failure;

        -- Operand B = +0.11000011 * 2^8.
        sw(9) <= '0';
        wait for 1 ns;
        assert ledr = "0000000000" severity failure;
        advance;

        -- F2: decimal 195 on HEX2..HEX0 and binary 11000011 on LEDR9..2.
        assert hex5 = segments("1111") severity failure;
        assert hex4 = segments("0010") severity failure;

        sw(9 downto 2) <= std_logic_vector(to_unsigned(195, 8));
        wait for 1 ns;
        assert hex2 = segments("0001") severity failure;
        assert hex1 = segments("1001") severity failure;
        assert hex0 = segments("0101") severity failure;
        assert ledr(9 downto 2) = std_logic_vector(to_unsigned(195, 8))
            severity failure;
        assert ledr(1 downto 0) = "00" severity failure;
        advance;

        -- E2: decimal 08 on HEX1..HEX0 and binary 1000 on LEDR9..6.
        assert hex5 = segments("1110") severity failure;
        assert hex4 = segments("0010") severity failure;

        sw(9 downto 6) <= std_logic_vector(to_unsigned(8, 4));
        wait for 1 ns;
        assert hex1 = segments("0000") severity failure;
        assert hex0 = segments("1000") severity failure;
        assert ledr(9 downto 6) = "1000" severity failure;
        assert ledr(5 downto 0) = "000000" severity failure;
        advance;

        -- Positive result in the book format:
        -- +0.11000011 * 2^8 + 0.11000011 * 2^8
        -- = +0.11000011 * 2^9. The result display reads "E9 F C3".
        assert hex5 = segments("1110") severity failure;
        assert hex4 = segments("1001") severity failure;
        assert hex3 = x"FF" severity failure;
        assert hex2 = segments("1111") severity failure;
        assert hex1 = segments("1100") severity failure;
        assert hex0 = segments("0011") severity failure;
        assert ledr(9) = '0' severity failure;
        assert ledr(8) = '1' severity failure;
        assert ledr(7 downto 0) = x"00"
            severity failure;

        -- Negative result: -0.10000000 * 2^0 plus zero. The result fields are
        -- exponent 0 and fraction 0x80; LEDR9 carries the negative sign.
        advance;
        enter_number('1', 128, 0);
        enter_number('0', 0, 0);

        assert hex5 = segments("1110") severity failure;
        assert hex4 = segments("0000") severity failure;
        assert hex3 = x"FF" severity failure;
        assert hex2 = segments("1111") severity failure;
        assert hex1 = segments("1000") severity failure;
        assert hex0 = segments("0000") severity failure;
        assert ledr(9) = '1'
            report "LEDR9 must be on for a negative result"
            severity failure;
        assert ledr(8) = '1' severity failure;
        assert ledr(7 downto 0) = x"00" severity failure;

        -- Literal book behavior for exact cancellation at exponent zero.
        -- The fraction and exponent clear, but sign_out keeps signb. Since the
        -- sorter selects the second equal-magnitude operand, LEDR9 stays on.
        advance;
        enter_number('0', 128, 0);
        enter_number('1', 128, 0);

        assert hex5 = segments("1110") severity failure;
        assert hex4 = segments("0000") severity failure;
        assert hex3 = x"FF" severity failure;
        assert hex2 = segments("1111") severity failure;
        assert hex1 = segments("0000") severity failure;
        assert hex0 = segments("0000") severity failure;
        assert ledr(9) = '1'
            report "Literal book zero keeps the selected big operand sign"
            severity failure;
        assert ledr(8) = '1' severity failure;
        assert ledr(7 downto 0) = x"00" severity failure;

        report "Board interface and book-format result display passed."
            severity note;
        finish;
    end process stimulus;
end architecture test;
