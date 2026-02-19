import os
import sys
import json
import time

from bitstream_builder import build_bitstream
from config_validation import validate_and_normalize_config

DEBUG_BITSTREAM_FILENAME = "bitstream.txt"


def _load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def _write_bitstream_text(path, bitstream, order="asc", m2k=False):
    if order not in ("asc", "desc"):
        raise ValueError("order must be 'asc' or 'desc'")
    iterable = reversed(bitstream) if order == "desc" else bitstream
    with open(path, "w") as f:
        if m2k:
            f.write("0\n")
        for bit in iterable:
            f.write("{}\n".format(int(bit)))


def _program_bitstream(bitstream, pin_en, pin_clk, pin_data, t_clk_half_cycle_us):
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


class MOSbiusV2Driver:
    def __init__(
        self,
        pin_en,
        pin_clk,
        pin_data,
        t_clk_half_cycle_us,
        config_file="config.json",
        pin_map_path=None,
        write_debug_bitstream=False,
    ):
        self.pin_en = pin_en
        self.pin_clk = pin_clk
        self.pin_data = pin_data
        self.t_clk_half_cycle_us = int(t_clk_half_cycle_us)
        self.config_file = config_file
        self.config_path = self._resolve_local_path(config_file)
        self.pin_map_path = pin_map_path or self._default_pin_map_path()
        self.write_debug_bitstream = write_debug_bitstream

    @staticmethod
    def _base_dir():
        if "__file__" in globals():
            return os.path.dirname(os.path.abspath(__file__))
        return "."

    @classmethod
    def _default_pin_map_path(cls):
        return os.path.join(cls._base_dir(), "chip_config_data", "pin_name_to_sw_matrix_pin_number.json")

    @classmethod
    def _resolve_local_path(cls, path):
        if os.path.isabs(path):
            return path
        return os.path.join(cls._project_dir(), path)

    @classmethod
    def _project_dir(cls):
        return os.path.dirname(cls._base_dir())

    def build_bitstream_from_config(self):
        config = _load_json(self.config_path)
        pin_to_sw_matrix = _load_json(self.pin_map_path)
        normalized = validate_and_normalize_config(config, pin_to_sw_matrix)
        bitstream = build_bitstream(
            normalized["connections"],
            normalized["sizes"],
            pin_to_sw_matrix,
            track_sources=self.write_debug_bitstream,
        )
        return bitstream

    def program_from_config(self):
        bitstream = self.build_bitstream_from_config()

        if self.write_debug_bitstream:
            debug_path = os.path.join(self._base_dir(), DEBUG_BITSTREAM_FILENAME)
            _write_bitstream_text(debug_path, bitstream, order="asc", m2k=False)

        if sys.implementation.name != "micropython":
            print("Generated {} bits (desktop mode, no GPIO programming)".format(len(bitstream)))
            return

        print("Programming bitstream")
        _program_bitstream(
            bitstream,
            self.pin_en,
            self.pin_clk,
            self.pin_data,
            t_clk_half_cycle_us=self.t_clk_half_cycle_us,
        )
        print("Programming completed")
