import os
import sys

from config_io import load_bitstream_text
from programmer import program_bitstream
from settings import EXPECTED_BITS, PIN_CLK, PIN_DATA, PIN_EN


def _default_bitstream_path():
    if "__file__" in globals():
        return os.path.join(os.path.dirname(__file__), "bitstream.txt")
    return "bitstream.txt"


def main(filename=None):
    if filename is None:
        filename = _default_bitstream_path()

    bitstream = load_bitstream_text(filename)
    if len(bitstream) != EXPECTED_BITS:
        print(
            "Warning: expected {} bits, loaded {} bits from {}".format(
                EXPECTED_BITS, len(bitstream), filename
            )
        )

    print("Programming bitstream")

    if sys.implementation.name != "micropython":
        print("Warning: GPIO pins not initialized. Abort programming.")
        return

    from machine import Pin

    pin_en = Pin(PIN_EN, Pin.OUT)
    pin_clk = Pin(PIN_CLK, Pin.OUT)
    pin_data = Pin(PIN_DATA, Pin.OUT)
    program_bitstream(bitstream, pin_en, pin_clk, pin_data)
    print("Programming completed")


if __name__ == "__main__":
    arg_filename = sys.argv[1] if len(sys.argv) > 1 else None
    main(arg_filename)
