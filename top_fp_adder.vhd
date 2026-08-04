library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity top_fp_adder is
    port (
        clk      : in  std_logic;                    -- 50 MHz board clock
        bt_clear : in  std_logic;                    -- KEY0, active low: go back
        bt_adv   : in  std_logic;                    -- KEY1, active low: confirm
        sw       : in  std_logic_vector(9 downto 0); -- slide switches SW9..SW0
        ledr     : out std_logic_vector(9 downto 0); -- red LEDs LEDR9..LEDR0
        hex0, hex1, hex2, hex3, hex4, hex5 : out std_logic_vector(7 downto 0)
    );
end entity top_fp_adder;

architecture rtl of top_fp_adder is
    -- [DE10-LITE ADAPTATION 1/4] A finite-state machine reuses the ten board
    -- switches to capture the 26 input bits as six consecutive fields.
    -- The six input states capture the sign, significand and exponent of
    -- operand A, then the same three fields of operand B. SHOW_RESULT keeps
    -- the computed value visible until the user advances or goes back.
    type state_type is (
        SET_SIGN_A, SET_SIG_A, SET_EXP_A,
        SET_SIGN_B, SET_SIG_B, SET_EXP_B,
        SHOW_RESULT
    );

    signal current_state : state_type := SET_SIGN_A;
    signal reg_a, reg_b  : unsigned(12 downto 0) := (others => '0');
    signal result        : unsigned(12 downto 0);

    -- Three samples per button: two flip-flops reduce metastability risk and
    -- the third sample provides one falling-edge pulse for each press.
    signal adv_sync, clear_sync : std_logic_vector(2 downto 0) := (others => '1');
    signal adv_edge, clear_edge : std_logic;

    signal disp_h0, disp_h1, disp_h2 : std_logic_vector(3 downto 0);
    signal disp_h3, disp_h4, disp_h5 : std_logic_vector(3 downto 0);
    signal blank_h0, blank_h1, blank_h2 : std_logic;
    signal blank_h3, blank_h4, blank_h5 : std_logic;
begin
    adder_inst : entity work.adder_unsigned(arch)
        port map (
            a   => reg_a,
            b   => reg_b,
            res => result
        );

    -- [DE10-LITE ADAPTATION 2/4] Push-buttons are active low and use Schmitt-
    -- trigger inputs in the QSF. The board provides hardware
    -- debouncing; these registers synchronize each asynchronous input to clk.
    process(clk)
    begin
        if rising_edge(clk) then
            adv_sync   <= adv_sync(1 downto 0) & bt_adv;
            clear_sync <= clear_sync(1 downto 0) & bt_clear;
        end if;
    end process;

    adv_edge   <= adv_sync(2) and not adv_sync(1);
    clear_edge <= clear_sync(2) and not clear_sync(1);

    -- [DE10-LITE ADAPTATION 3/4] Input-state register. bt_adv confirms and
    -- stores the current field; bt_clear moves back so it can be corrected.
    process(clk)
    begin
        if rising_edge(clk) then
            if clear_edge = '1' then
                case current_state is
                    when SET_SIG_A   => current_state <= SET_SIGN_A;
                    when SET_EXP_A   => current_state <= SET_SIG_A;
                    when SET_SIGN_B  => current_state <= SET_EXP_A;
                    when SET_SIG_B   => current_state <= SET_SIGN_B;
                    when SET_EXP_B   => current_state <= SET_SIG_B;
                    when SHOW_RESULT => current_state <= SET_EXP_B;
                    when others      => current_state <= SET_SIGN_A;
                end case;
            elsif adv_edge = '1' then
                case current_state is
                    when SET_SIGN_A =>
                        reg_a(12) <= sw(9); -- 0 = positive/zero; 1 = negative
                        current_state <= SET_SIG_A;
                    when SET_SIG_A =>
                        reg_a(7 downto 0) <= unsigned(sw(9 downto 2));
                        current_state <= SET_EXP_A;
                    when SET_EXP_A =>
                        reg_a(11 downto 8) <= unsigned(sw(9 downto 6));
                        current_state <= SET_SIGN_B;
                    when SET_SIGN_B =>
                        reg_b(12) <= sw(9); -- 0 = positive/zero; 1 = negative
                        current_state <= SET_SIG_B;
                    when SET_SIG_B =>
                        reg_b(7 downto 0) <= unsigned(sw(9 downto 2));
                        current_state <= SET_EXP_B;
                    when SET_EXP_B =>
                        reg_b(11 downto 8) <= unsigned(sw(9 downto 6));
                        current_state <= SHOW_RESULT;
                    when SHOW_RESULT =>
                        current_state <= SET_SIGN_A;
                end case;
            end if;
        end if;
    end process;

    -- [DE10-LITE ADAPTATION 4/4] Combinational user interface:
    --   * HEX5..HEX4 identify the current field as S1, F1, E1, S2, F2 or E2.
    --   * Lower displays show decimal input values: sign 0..1, significand
    --     000..255 and exponent 00..15.
    --   * During input, LEDs mirror only the switches used by that field.
    --   * In SHOW_RESULT, the displays expose the normalized book fields as
    --     E<exponent> F<fraction>; LEDR9 is sign and LEDR8 marks validity.
    process(all)
        variable input_value : natural range 0 to 255;
    begin
        input_value := 0;
        disp_h5 <= "0000";
        disp_h4 <= "0000";
        disp_h3 <= "0000";
        disp_h2 <= "0000";
        disp_h1 <= "0000";
        disp_h0 <= "0000";
        blank_h5 <= '1';
        blank_h4 <= '1';
        blank_h3 <= '1';
        blank_h2 <= '1';
        blank_h1 <= '1';
        blank_h0 <= '1';
        ledr <= (others => '0');

        case current_state is
            when SET_SIGN_A =>
                disp_h5 <= "0101"; -- Digit 5 is used as a seven-segment S.
                disp_h4 <= "0001";
                disp_h0 <= "000" & sw(9);
                ledr(9) <= sw(9);
                blank_h5 <= '0';
                blank_h4 <= '0';
                blank_h0 <= '0';

            when SET_SIG_A =>
                input_value := to_integer(unsigned(sw(9 downto 2)));
                disp_h5 <= "1111"; -- Hexadecimal F labels the significand.
                disp_h4 <= "0001";
                disp_h2 <= std_logic_vector(to_unsigned(input_value / 100, 4));
                disp_h1 <= std_logic_vector(to_unsigned((input_value / 10) mod 10, 4));
                disp_h0 <= std_logic_vector(to_unsigned(input_value mod 10, 4));
                ledr(9 downto 2) <= sw(9 downto 2);
                blank_h5 <= '0';
                blank_h4 <= '0';
                blank_h2 <= '0';
                blank_h1 <= '0';
                blank_h0 <= '0';

            when SET_EXP_A =>
                input_value := to_integer(unsigned(sw(9 downto 6)));
                disp_h5 <= "1110"; -- Hexadecimal E labels the exponent.
                disp_h4 <= "0001";
                disp_h1 <= std_logic_vector(to_unsigned(input_value / 10, 4));
                disp_h0 <= std_logic_vector(to_unsigned(input_value mod 10, 4));
                ledr(9 downto 6) <= sw(9 downto 6);
                blank_h5 <= '0';
                blank_h4 <= '0';
                blank_h1 <= '0';
                blank_h0 <= '0';

            when SET_SIGN_B =>
                disp_h5 <= "0101"; -- Digit 5 is used as a seven-segment S.
                disp_h4 <= "0010";
                disp_h0 <= "000" & sw(9);
                ledr(9) <= sw(9);
                blank_h5 <= '0';
                blank_h4 <= '0';
                blank_h0 <= '0';

            when SET_SIG_B =>
                input_value := to_integer(unsigned(sw(9 downto 2)));
                disp_h5 <= "1111"; -- Hexadecimal F labels the significand.
                disp_h4 <= "0010";
                disp_h2 <= std_logic_vector(to_unsigned(input_value / 100, 4));
                disp_h1 <= std_logic_vector(to_unsigned((input_value / 10) mod 10, 4));
                disp_h0 <= std_logic_vector(to_unsigned(input_value mod 10, 4));
                ledr(9 downto 2) <= sw(9 downto 2);
                blank_h5 <= '0';
                blank_h4 <= '0';
                blank_h2 <= '0';
                blank_h1 <= '0';
                blank_h0 <= '0';

            when SET_EXP_B =>
                input_value := to_integer(unsigned(sw(9 downto 6)));
                disp_h5 <= "1110"; -- Hexadecimal E labels the exponent.
                disp_h4 <= "0010";
                disp_h1 <= std_logic_vector(to_unsigned(input_value / 10, 4));
                disp_h0 <= std_logic_vector(to_unsigned(input_value mod 10, 4));
                ledr(9 downto 6) <= sw(9 downto 6);
                blank_h5 <= '0';
                blank_h4 <= '0';
                blank_h1 <= '0';
                blank_h0 <= '0';

            when SHOW_RESULT =>
                -- Example: sign=1, exponent=4, fraction=0x99 is displayed as
                -- "E4 F99" with LEDR9 on. HEX3 is the visual separator.
                disp_h5 <= "1110"; -- E
                disp_h4 <= std_logic_vector(result(11 downto 8));
                disp_h2 <= "1111"; -- F
                disp_h1 <= std_logic_vector(result(7 downto 4));
                disp_h0 <= std_logic_vector(result(3 downto 0));
                blank_h5 <= '0';
                blank_h4 <= '0';
                blank_h2 <= '0';
                blank_h1 <= '0';
                blank_h0 <= '0';

                ledr(9) <= result(12); -- mirrors sign_out, including signed zero
                ledr(8) <= '1';        -- asserted only when result is valid
                -- LEDR7..LEDR0 are reserved and remain off in this state.
        end case;
    end process;

    sseg0 : entity work.hex_to_sseg(hex_to_sseg_arch)
        port map (hex => disp_h0, dp => '1', blank => blank_h0, sseg => hex0);
    sseg1 : entity work.hex_to_sseg(hex_to_sseg_arch)
        port map (hex => disp_h1, dp => '1', blank => blank_h1, sseg => hex1);
    sseg2 : entity work.hex_to_sseg(hex_to_sseg_arch)
        port map (hex => disp_h2, dp => '1', blank => blank_h2, sseg => hex2);
    sseg3 : entity work.hex_to_sseg(hex_to_sseg_arch)
        port map (hex => disp_h3, dp => '1', blank => blank_h3, sseg => hex3);
    sseg4 : entity work.hex_to_sseg(hex_to_sseg_arch)
        port map (hex => disp_h4, dp => '1', blank => blank_h4, sseg => hex4);
    sseg5 : entity work.hex_to_sseg(hex_to_sseg_arch)
        port map (hex => disp_h5, dp => '1', blank => blank_h5, sseg => hex5);
end architecture rtl;
