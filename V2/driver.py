import os
import sys

from bitstream_builder import build_bitstream
from config_io import load_json, write_bitstream_text
from config_validation import validate_and_normalize_config
from programmer import program_bitstream
from settings import DEBUG_BITSTREAM_FILENAME


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
    def default_config_path(cls):
        return os.path.join(cls._base_dir(), "config.json")

    @classmethod
    def _default_pin_map_path(cls):
        return os.path.join(cls._base_dir(), "chip_config_data", "pin_name_to_sw_matrix_pin_number.json")

    @classmethod
    def _resolve_local_path(cls, relative_path):
        return os.path.join(cls._base_dir(), relative_path)

    def build_bitstream_from_config(self):
        config = load_json(self.config_path)
        pin_to_sw_matrix = load_json(self.pin_map_path)
        normalized = validate_and_normalize_config(config, pin_to_sw_matrix)
        bitstream = build_bitstream(normalized["connections"], normalized["sizes"], pin_to_sw_matrix)
        return bitstream

    def program_from_config(self):
        bitstream = self.build_bitstream_from_config()

        if self.write_debug_bitstream:
            debug_path = os.path.join(self._base_dir(), DEBUG_BITSTREAM_FILENAME)
            write_bitstream_text(debug_path, bitstream, order="asc", m2k=False)

        if sys.implementation.name != "micropython":
            print("Generated {} bits (desktop mode, no GPIO programming)".format(len(bitstream)))
            return

        print("Programming bitstream")
        program_bitstream(
            bitstream,
            self.pin_en,
            self.pin_clk,
            self.pin_data,
            t_clk_half_cycle_us=self.t_clk_half_cycle_us,
        )
        print("Programming completed")
