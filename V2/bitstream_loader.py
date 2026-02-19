import os
import sys
import time

PIN_EN = 18
PIN_CLK = 17
PIN_DATA = 16

EXPECTED_BITS = 2008
T_CLK_HALF_CYCLE_US = 100


class mosbius_mk2:
    def __init__(self, pin_en=None, pin_clk=None, pin_data=None):
        self.pin_en = pin_en
        self.pin_clk = pin_clk
        self.pin_data = pin_data
        self.bitstream = []

    def load_bitstream_from_file(self, filename):
        bits = []
        with open(filename, "r") as file:
            for line_no, raw_line in enumerate(file, 1):
                line = raw_line.strip()
                if not line:
                    continue
                if line not in ("0", "1"):
                    raise ValueError(
                        "Invalid bitstream value '{}' at line {} in {}".format(
                            line, line_no, filename
                        )
                    )
                bits.append(1 if line == "1" else 0)

        if not bits:
            raise ValueError("Bitstream file is empty: {}".format(filename))

        self.bitstream = bits
        if len(self.bitstream) != EXPECTED_BITS:
            print(
                "Warning: expected {} bits, loaded {} bits from {}".format(
                    EXPECTED_BITS, len(self.bitstream), filename
                )
            )

    def program_bitstream(self):
        print("Programming bitstream")

        if self.pin_en is None or self.pin_clk is None or self.pin_data is None:
            print("Warning: GPIO pins not initialized. Abort programming.")
            return

        if not self.bitstream:
            raise ValueError("Bitstream is empty. Load bitstream before programming.")

        self.pin_data.value(0)
        self.pin_clk.value(0)
        self.pin_en.value(0)

        # V2 generator default is ascending register order; shift MSB-last like V1.
        for bit in reversed(self.bitstream):
            self.pin_data.value(bit)
            self.pin_clk.value(1)
            time.sleep_us(T_CLK_HALF_CYCLE_US)
            self.pin_clk.value(0)
            time.sleep_us(T_CLK_HALF_CYCLE_US)

        self.pin_en.value(1)
        print("Programming completed")


def _default_bitstream_path():
    if "__file__" in globals():
        return os.path.join(os.path.dirname(__file__), "bitstream.txt")
    return "bitstream.txt"


def main(filename=None):
    if filename is None:
        filename = _default_bitstream_path()

    if sys.implementation.name == "micropython":
        from machine import Pin

        pin_en = Pin(PIN_EN, Pin.OUT)
        pin_clk = Pin(PIN_CLK, Pin.OUT)
        pin_data = Pin(PIN_DATA, Pin.OUT)
        chip = mosbius_mk2(pin_en, pin_clk, pin_data)
    else:
        chip = mosbius_mk2()

    chip.load_bitstream_from_file(filename)
    chip.program_bitstream()


if __name__ == "__main__":
    arg_filename = sys.argv[1] if len(sys.argv) > 1 else None
    main(arg_filename)
