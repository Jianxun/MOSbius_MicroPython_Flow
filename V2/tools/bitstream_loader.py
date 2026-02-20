import os
import sys
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LIB_DIR = os.path.join(os.path.dirname(BASE_DIR), "lib")
sys.path.insert(0, LIB_DIR)

from bitstream_builder import EXPECTED_BITS

DEFAULT_PIN_EN = 18
DEFAULT_PIN_CLK = 17
DEFAULT_PIN_DATA = 16
DEFAULT_T_CLK_HALF_CYCLE_US = 10


def _load_bitstream_text(path):
    bits = []
    with open(path, "r") as f:
        for line_no, raw_line in enumerate(f, 1):
            line = raw_line.strip()
            if not line:
                continue
            if line not in ("0", "1"):
                raise ValueError(
                    "Invalid bitstream value '{}' at line {} in {}".format(
                        line, line_no, path
                    )
                )
            bits.append(1 if line == "1" else 0)
    if not bits:
        raise ValueError("Bitstream file is empty: {}".format(path))
    return bits


def _program_bitstream(bitstream, pin_en, pin_clk, pin_data, t_clk_half_cycle_us):
    if pin_en is None or pin_clk is None or pin_data is None:
        raise ValueError("GPIO pins are not initialized")
    if not bitstream:
        raise ValueError("Bitstream is empty")

    pin_data.value(0)
    pin_clk.value(0)
    pin_en.value(0)

    for bit in reversed(bitstream):
        pin_data.value(bit)
        pin_clk.value(1)
        time.sleep_us(t_clk_half_cycle_us)
        pin_clk.value(0)
        time.sleep_us(t_clk_half_cycle_us)

    pin_en.value(1)


def _default_bitstream_path():
    return os.path.join(BASE_DIR, "bitstream.txt")


def _usage():
    script = os.path.basename(sys.argv[0])
    return (
        "Usage: {} [bitstream.txt] [--pin-en N] [--pin-clk N] [--pin-data N] [--t-half-us N]\\n".format(script)
    )


def _parse_args(argv):
    filename = None
    pin_en = DEFAULT_PIN_EN
    pin_clk = DEFAULT_PIN_CLK
    pin_data = DEFAULT_PIN_DATA
    t_half_us = DEFAULT_T_CLK_HALF_CYCLE_US

    positionals = []
    i = 1
    while i < len(argv):
        arg = argv[i]
        if arg in ("-h", "--help"):
            print(_usage())
            raise SystemExit(0)
        if arg in ("--pin-en", "--pin-clk", "--pin-data", "--t-half-us"):
            if i + 1 >= len(argv):
                raise ValueError("Missing value for {}".format(arg))
            value = int(argv[i + 1])
            if arg == "--pin-en":
                pin_en = value
            elif arg == "--pin-clk":
                pin_clk = value
            elif arg == "--pin-data":
                pin_data = value
            else:
                t_half_us = value
            i += 1
        elif arg.startswith("--pin-en="):
            pin_en = int(arg.split("=", 1)[1].strip())
        elif arg.startswith("--pin-clk="):
            pin_clk = int(arg.split("=", 1)[1].strip())
        elif arg.startswith("--pin-data="):
            pin_data = int(arg.split("=", 1)[1].strip())
        elif arg.startswith("--t-half-us="):
            t_half_us = int(arg.split("=", 1)[1].strip())
        else:
            positionals.append(arg)
        i += 1

    if len(positionals) > 1:
        raise ValueError("Too many positional arguments")
    if positionals:
        filename = positionals[0]
    return filename, pin_en, pin_clk, pin_data, t_half_us


def main():
    filename, pin_en_num, pin_clk_num, pin_data_num, t_half_us = _parse_args(sys.argv)
    if filename is None:
        filename = _default_bitstream_path()

    bitstream = _load_bitstream_text(filename)
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

    pin_en = Pin(pin_en_num, Pin.OUT)
    pin_clk = Pin(pin_clk_num, Pin.OUT)
    pin_data = Pin(pin_data_num, Pin.OUT)
    _program_bitstream(
        bitstream,
        pin_en,
        pin_clk,
        pin_data,
        t_clk_half_cycle_us=t_half_us,
    )
    print("Programming completed")


if __name__ == "__main__":
    main()
