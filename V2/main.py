import os
import sys

from bitstream_builder import build_bitstream
from config_io import load_json, write_bitstream_text
from config_validation import validate_and_normalize_config
from programmer import program_bitstream
from settings import DEBUG_BITSTREAM_FILENAME, PIN_CLK, PIN_DATA, PIN_EN


def _base_dir():
    if "__file__" in globals():
        return os.path.dirname(os.path.abspath(__file__))
    return "."


def run(config_path=None, write_debug_bitstream=False):
    base_dir = _base_dir()
    if config_path is None:
        config_path = os.path.join(base_dir, "config.json")

    pin_map_path = os.path.join(base_dir, "chip_config_data", "pin_name_to_sw_matrix_pin_number.json")
    config = load_json(config_path)
    pin_to_sw_matrix = load_json(pin_map_path)
    normalized = validate_and_normalize_config(config, pin_to_sw_matrix)
    bitstream = build_bitstream(normalized["connections"], normalized["sizes"], pin_to_sw_matrix)

    if write_debug_bitstream:
        debug_path = os.path.join(base_dir, DEBUG_BITSTREAM_FILENAME)
        write_bitstream_text(debug_path, bitstream, order="asc", m2k=False)

    if sys.implementation.name != "micropython":
        print("Generated {} bits (desktop mode, no GPIO programming)".format(len(bitstream)))
        return 0

    from machine import Pin

    pin_en = Pin(PIN_EN, Pin.OUT)
    pin_clk = Pin(PIN_CLK, Pin.OUT)
    pin_data = Pin(PIN_DATA, Pin.OUT)

    print("Programming bitstream")
    program_bitstream(bitstream, pin_en, pin_clk, pin_data)
    print("Programming completed")
    return 0


def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else None
    return run(config_path=config_path, write_debug_bitstream=False)


if __name__ == "__main__":
    raise SystemExit(main())
