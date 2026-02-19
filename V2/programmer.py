import time

from settings import T_CLK_HALF_CYCLE_US


def program_bitstream(bitstream, pin_en, pin_clk, pin_data, t_clk_half_cycle_us=T_CLK_HALF_CYCLE_US):
    if pin_en is None or pin_clk is None or pin_data is None:
        raise ValueError("GPIO pins are not initialized")
    if not bitstream:
        raise ValueError("Bitstream is empty")

    pin_data.value(0)
    pin_clk.value(0)
    pin_en.value(0)

    # Bitstream is generated in ascending register order; shift last bit first.
    for bit in reversed(bitstream):
        pin_data.value(bit)
        pin_clk.value(1)
        time.sleep_us(t_clk_half_cycle_us)
        pin_clk.value(0)
        time.sleep_us(t_clk_half_cycle_us)

    pin_en.value(1)
