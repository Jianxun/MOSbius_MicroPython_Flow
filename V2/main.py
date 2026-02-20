import sys
import os

def _dirname(path):
    if not path:
        return "."
    if "/" not in path:
        return "."
    head = path.rsplit("/", 1)[0]
    return head if head else "/"


def _join(a, b):
    if not a or a == ".":
        return b
    if a.endswith("/"):
        return a + b
    return a + "/" + b


def _isabs(path):
    return isinstance(path, str) and path.startswith("/")


def _resolve_base_dir():
    base_dir = _dirname(globals().get("__file__", ""))
    if base_dir != ".":
        return base_dir

    argv0 = sys.argv[0] if len(sys.argv) > 0 else ""
    argv_dir = _dirname(argv0)
    if argv_dir != ".":
        return argv_dir

    try:
        return os.getcwd()
    except Exception:
        return "."


BASE_DIR = _resolve_base_dir()
sys.path.insert(0, _join(BASE_DIR, "lib"))
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

    config_path = CONFIG_FILE if _isabs(CONFIG_FILE) else _join(BASE_DIR, CONFIG_FILE)
    pin_map_path = _join(BASE_DIR, "lib/pin_name_to_sw_matrix_pin_number.json")

    driver = MOSbiusV2Driver(
        pin_en=pin_en,
        pin_clk=pin_clk,
        pin_data=pin_data,
        t_clk_half_cycle_us=T_CLK_HALF_CYCLE_US,
        config_file=config_path,
        pin_map_path=pin_map_path,
    )
    print("Using config: {}".format(driver.config_path))
    driver.program_from_config()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
