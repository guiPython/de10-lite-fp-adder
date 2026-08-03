library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity adder_unsigned_testbench is
end entity adder_unsigned_testbench;

architecture test of adder_unsigned_testbench is
    signal a, b : unsigned(12 downto 0) := (others => '0');
    signal res  : unsigned(12 downto 0);

    -- Build a 13-bit number: [sign | exponent | fractional]
    function number(
        sig : std_logic;
        fractional : natural;
        expoent  : natural
    ) return unsigned is
        variable value : unsigned(12 downto 0);
    begin
        value(12)          := sig;
        value(11 downto 8) := to_unsigned(expoent, 4);
        value(7 downto 0)  := to_unsigned(fractional, 8);
        return value;
    end function;
begin
    uut : entity work.adder_unsigned(arch)
        port map (
            a   => a,
            b   => b,
            res => res
        );

    stimulus : process
    begin
        -- Case 1: Different exponents and opposite signs. (Sort | Align | Subtraction)
        a <= number('0', 138, 3);
        b <= number('1', 222, 4);
        wait for 200 ns;

        assert res = number('1', 153, 4)
            report "ERROR: expect 1010010011001"
            severity error;

        -- Case 2: Subtraction followed by a left shift.
        a <= number('1', 144, 3);
        b <= number('0', 128, 3);
        wait for 200 ns;

        assert res = number('1', 128, 0)
            report "ERROR: expect 1000010000000"
            severity error;

        -- Case 3: Underflow according to the original implementation.
        a <= number('1', 129, 0);
        b <= number('0', 128, 0);
        wait for 200 ns;

        assert res = number('1', 0, 0)
            report "ERROR: expect 1000000000000"
            severity error;

        -- Case 4: Addition with carry and right shift.
        a <= number('0', 144, 3);
        b <= number('0', 128, 3);
        wait for 200 ns;

        assert res = number('0', 136, 4)
            report "ERROR: expect 0010010001000"
            severity error;

        report "All original test cases passed."
            severity note;

        wait;
    end process stimulus;
end architecture test;
