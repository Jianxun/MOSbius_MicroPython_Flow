import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else "."
sys.path.insert(0, os.path.join(BASE_DIR, "lib"))
from driver import MOSbiusV2Driver

# User-editable settings.
PIN_EN = 18
PIN_CLK = 17
PIN_DATA = 16
T_CLK_HALF_CYCLE_US = 10
CONFIG_FILE = "config.json"


def main():
    if sys.implementation.name == "micropython":
        from machine import Pin

        pin_en = Pin(PIN_EN, Pin.OUT)
        pin_clk = Pin(PIN_CLK, Pin.OUT)
        pin_data = Pin(PIN_DATA, Pin.OUT)
    else:
        pin_en = None
        pin_clk = None
        pin_data = None

    driver = MOSbiusV2Driver(
        pin_en=pin_en,
        pin_clk=pin_clk,
        pin_data=pin_data,
        t_clk_half_cycle_us=T_CLK_HALF_CYCLE_US,
        config_file=CONFIG_FILE,
    )
    print("Using config: {}".format(driver.config_path))
    driver.program_from_config()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
