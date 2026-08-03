library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity adder_unsigned is
    port (
        -- 13 bits numbers [sign | exp => [11..8] | frac => [7..0]]
        a, b : in unsigned (12 downto 0);

        -- 13 bits numbers [sign | exp => [11..8] | frac => [7..0]]
        res : out unsigned (12 downto 0)
    );
end adder_unsigned;

architecture arch of adder_unsigned is
    -- 13 bits numbers [sign | exp => [11..8] | frac => [7..0]]
    signal big, small, normalized : unsigned (12 downto 0);
    -- 8 bits to align smallest fractional part
    signal aligned : unsigned (7 downto 0);
    -- 9 bits to sum [overflow | frac => [7..0]]
    signal sum : unsigned (8 downto 0);
    -- 7 because we can have a maximum of 7 leading zeros
    signal leading_zeros : integer range 0 to 7;

    -- Extract sign from 13 bits numbers
    function sig(n : unsigned(12 downto 0)) return std_logic is
    begin
        return n(12);
    end function;

    -- Extract expoent from 13 bits numbers
    function expoent(n : unsigned(12 downto 0)) return unsigned is
    begin
        return n(11 downto 8);
    end function;

    -- Extract fractional part from 13 bits numbers
    function fractional(n : unsigned(12 downto 0)) return unsigned is
    begin
        return n(7 downto 0);
    end function;

begin
    -- 1st stage : sort to find the larger number
    process (a, b)
    begin
        if expoent(a) & fractional(a) > expoent(b) & fractional(b) then
            big <= a;
            small <= b;
        else
            big <= b;
            small <= a;
        end if;
    end process;

    -- 2nd stage : align smaller number
    -- shift right divide by 2, x times, increasing the exponent of the smaller number x times
    -- where x is the difference between the exponents
    aligned <= shift_right(fractional(small), to_integer(expoent(big) - expoent(small)));

    -- 3rd stage : add / subtract
    sum <= ('0' & fractional(big)) + ('0' & aligned) when sig(big) = sig(small) else
           ('0' & fractional(big)) - ('0' & aligned);

    -- 4th stage : count leading 0s
    leading_zeros <= 0 when (sum (7) = '1') else
                     1 when (sum (6) = '1') else
                     2 when (sum (5) = '1') else
                     3 when (sum (4) = '1') else
                     4 when (sum (3) = '1') else
                     5 when (sum (2) = '1') else
                     6 when (sum (1) = '1') else
                     7;

    -- 5th stage : normalize with special conditions
    process (big, sum, leading_zeros)
        variable big_expoent : integer;
    begin
        big_expoent := to_integer(expoent(big));
        -- set signal
        normalized(12) <= sig(big);
        if sum (8) = '1' then
            -- if overflow bit is one shift_left sum and increase expoent
            -- set expoent with big expoent + 1
            normalized(11 downto 8) <= to_unsigned(big_expoent + 1, 4);
            -- set fractional with sum * 2 <=> shift left 1 bit
            normalized(7 downto 0) <= sum(8 downto 1);
        elsif (leading_zeros > expoent(big)) OR sum = 0 then
            -- if leading_zeros greater than big expoent underfow
            -- the exponent is not large enough to support sucessive shift right without becoming negative
            -- set expoent and fractional part with zero`s
            normalized(11 downto 0) <= (others => '0');
        else
            -- else no overflow occurred, and we can normalize the result of the sum
            -- set expoent with big expoent minus leading_zeros because normalized is the shift righted sum.
            normalized(11 downto 8) <= to_unsigned(big_expoent - leading_zeros, 4);
            -- set fractional part with normalized sum making
            normalized(7 downto 0) <= shift_left(sum(7 downto 0), leading_zeros);
        end if;
    end process;

    -- form output --
    res <= normalized;
end arch;
