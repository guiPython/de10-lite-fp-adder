library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity adder_unsigned is
    port (
        -- Packed 13-bit book format: [sign(1) | exponent(4) | fraction(8)].
        -- Numeric value: (-1)^sign * 0.fraction * 2^exponent.
        a, b      : in  unsigned(12 downto 0);
        res       : out unsigned(12 downto 0);
        underflow : out std_logic;
        overflow  : out std_logic
    );
end entity adder_unsigned;

architecture arch of adder_unsigned is
    -- The packed implementation follows the same stages as Listing 3.19.
    -- Suffix-free names are retained from the student implementation.
    signal big, small, normalized : unsigned(12 downto 0);
    signal aligned               : unsigned(7 downto 0);
    signal sum                   : unsigned(8 downto 0);
    signal leading_zeros         : natural range 0 to 7;

    -- Extract the sign field from a packed 13-bit number.
    function sign_of(number : unsigned(12 downto 0)) return std_logic is
    begin
        return number(12);
    end function;

    -- Extract the unsigned four-bit exponent field.
    function exponent_of(number : unsigned(12 downto 0)) return unsigned is
    begin
        return number(11 downto 8);
    end function;

    -- Extract the eight-bit fraction field.
    function fraction_of(number : unsigned(12 downto 0)) return unsigned is
    begin
        return number(7 downto 0);
    end function;
begin
    -- 1st stage: sort by magnitude. As in the book, B is selected as the
    -- larger operand when both exponent/fraction fields are equal.
    process(a, b)
    begin
        if (exponent_of(a) & fraction_of(a)) >
           (exponent_of(b) & fraction_of(b)) then
            big   <= a;
            small <= b;
        else
            big   <= b;
            small <= a;
        end if;
    end process;

    -- 2nd stage: align the smaller fraction with the larger exponent.
    aligned <= shift_right(
        fraction_of(small),
        to_integer(exponent_of(big) - exponent_of(small))
    );

    -- 3rd stage: add equal signs or subtract opposite signs. The ninth bit is
    -- only an internal carry bit; inputs and result remain 13 bits wide.
    sum <= ('0' & fraction_of(big)) + ('0' & aligned)
           when sign_of(big) = sign_of(small) else
           ('0' & fraction_of(big)) - ('0' & aligned);

    -- 4th stage, part A: count up to seven leading zeros in sum(7 downto 0).
    -- The priority encoder returns seven for both 00000001 and 00000000,
    -- exactly like the original circuit from the book.
    leading_zeros <= 0 when sum(7) = '1' else
                     1 when sum(6) = '1' else
                     2 when sum(5) = '1' else
                     3 when sum(4) = '1' else
                     4 when sum(3) = '1' else
                     5 when sum(2) = '1' else
                     6 when sum(1) = '1' else
                     7;

    -- 4th stage, part B: normalize the 13-bit result and expose the two range
    -- conditions needed by the board. These flags describe whether the exact
    -- nonzero result was lost below exponent zero or above exponent fifteen;
    -- they do not change the literal result produced by the book algorithm.
    process(big, sum, leading_zeros)
    begin
        normalized(12) <= sign_of(big);
        underflow <= '0';
        overflow  <= '0';

        if sum(8) = '1' then
            -- Carry normalization shifts right and increments the four-bit
            -- exponent. At exponent 15 the book result wraps to zero.
            normalized(11 downto 8) <= exponent_of(big) + 1;
            normalized(7 downto 0)  <= sum(8 downto 1);

            if exponent_of(big) = "1111" then
                overflow <= '1';
            end if;
        elsif leading_zeros > to_integer(exponent_of(big)) then
            normalized(11 downto 0) <= (others => '0');

            -- Exact cancellation is a valid zero. Underflow is asserted only
            -- when normalization discards a nonzero mathematical result.
            if sum /= to_unsigned(0, sum'length) then
                underflow <= '1';
            end if;
        else
            normalized(11 downto 8) <=
                exponent_of(big) - to_unsigned(leading_zeros, 4);
            normalized(7 downto 0) <=
                shift_left(sum(7 downto 0), leading_zeros);
        end if;
    end process;

    -- The external arithmetic result remains the original packed 13-bit word.
    res <= normalized;
end architecture arch;
