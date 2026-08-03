library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use std.env.all;

entity adder_unsigned_testbench is
end entity adder_unsigned_testbench;

architecture test of adder_unsigned_testbench is
    signal a, b                 : unsigned(12 downto 0) := (others => '0');
    signal res                  : unsigned(12 downto 0);
    signal underflow, overflow  : std_logic;
    signal test_index           : natural := 0;

    -- Build one packed book-format number: [sign | exponent | fraction].
    function number(
        sign_bit : std_logic;
        fraction : natural;
        exponent : natural
    ) return unsigned is
        variable value : unsigned(12 downto 0);
    begin
        assert fraction <= 255
            report "Fraction is outside the 8-bit range"
            severity failure;
        assert exponent <= 15
            report "Exponent is outside the 4-bit range"
            severity failure;

        value(12)          := sign_bit;
        value(11 downto 8) := to_unsigned(exponent, 4);
        value(7 downto 0)  := to_unsigned(fraction, 8);
        return value;
    end function;
begin
    uut : entity work.adder_unsigned(arch)
        port map (
            a => a, b => b, res => res,
            underflow => underflow,
            overflow => overflow
        );

    stimulus : process
        variable tests_run : natural := 0;

        procedure check(
            constant description : string;
            constant operand_a   : unsigned(12 downto 0);
            constant operand_b   : unsigned(12 downto 0);
            constant expected    : unsigned(12 downto 0);
            constant expected_underflow : std_logic := '0';
            constant expected_overflow  : std_logic := '0'
        ) is
        begin
            a <= operand_a;
            b <= operand_b;
            test_index <= tests_run + 1;
            wait for 1 ns;

            assert res = expected
                report description & ": actual=0x" & to_hstring(res) &
                       ", expected=0x" & to_hstring(expected)
                severity failure;
            assert underflow = expected_underflow
                report description & ": unexpected underflow status"
                severity failure;
            assert overflow = expected_overflow
                report description & ": unexpected overflow status"
                severity failure;

            tests_run := tests_run + 1;
        end procedure;
    begin
        -- Case 1 - book example: sort, align and subtract.
        -- +0.10001010 * 2^3 - 0.11011110 * 2^4
        -- = -0.10011001 * 2^4.
        check("different exponents and opposite signs",
              number('0', 138, 3), number('1', 222, 4),
              number('1', 153, 4));

        -- Case 2 - three leading zeros require three left shifts.
        -- -0.10010000 * 2^3 + 0.10000000 * 2^3
        -- = -0.10000000 * 2^0.
        check("subtraction followed by left normalization",
              number('1', 144, 3), number('0', 128, 3),
              number('1', 128, 0));

        -- Case 3 - the result would need a negative exponent and underflows.
        check("book underflow behavior",
              number('1', 129, 0), number('0', 128, 0),
              number('1', 0, 0), expected_underflow => '1');

        -- Case 4 - carry-out shifts the fraction right and increments exponent.
        check("addition with carry and right normalization",
              number('0', 144, 3), number('0', 128, 3),
              number('0', 136, 4));

        -- Case 5 - exactly seven leading zeros can still normalize at e=7.
        check("seven leading zeros at the exponent boundary",
              number('0', 129, 7), number('1', 128, 7),
              number('0', 128, 0));

        -- Case 6 - the same one-bit difference underflows when e=6.
        check("seven leading zeros below the exponent boundary",
              number('0', 129, 6), number('1', 128, 6),
              number('0', 0, 0), expected_underflow => '1');

        -- Case 7 - exact cancellation at a low exponent takes the book's
        -- zero-producing branch. It yields -0 but does not assert underflow,
        -- because no nonzero mathematical result was discarded.
        check("exact cancellation at low exponent",
              number('0', 128, 3), number('1', 128, 3),
              number('1', 0, 0));

        -- Case 8 - literal Listing 3.19 limitation: sum=0 and sum=1 both set
        -- leado=7. At e=8, zero therefore leaves exponent 1 instead of 0.
        check("exact cancellation exposes zero-count ambiguity",
              number('0', 128, 8), number('1', 128, 8),
              number('1', 0, 1));

        -- Case 9 - same-sign negative addition preserves the negative sign.
        check("two negative operands with carry",
              number('1', 144, 3), number('1', 128, 3),
              number('1', 136, 4));

        -- Case 10 - an exponent difference of eight shifts every bit of the
        -- smaller operand out before the addition, as specified by the book.
        check("alignment discards an operand eight exponents smaller",
              number('0', 128, 8), number('0', 255, 0),
              number('0', 128, 8));

        -- Case 11 - a carry at e=15 wraps the literal four-bit result exponent
        -- to zero and asserts the added overflow status output.
        check("literal exponent-overflow behavior",
              number('0', 255, 15), number('0', 255, 15),
              number('0', 255, 0), expected_overflow => '1');

        report "All " & integer'image(tests_run) &
               " book-compatible packed test cases passed."
            severity note;
        finish;
    end process stimulus;
end architecture test;
