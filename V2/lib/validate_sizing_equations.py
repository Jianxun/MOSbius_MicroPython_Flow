import argparse
import json
from pathlib import Path


BIT_WEIGHTS = (1, 2, 4, 8, 16)
BASE_REGISTER = 1889
BITS_PER_DEVICE = 5


def _default_map_path():
    return Path(__file__).resolve().parent / "chip_config_data" / "device_name_to_sizing_registers.json"


def _fail(message):
    raise ValueError(message)


def _parse_int_register(raw_value, device, bit_weight):
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        _fail(
            "non-integer register value at device '{}' bit '{}': {!r}".format(
                device, bit_weight, raw_value
            )
        )


def _expected_register(device_index, bit_index):
    return BASE_REGISTER + BITS_PER_DEVICE * device_index + bit_index


def _load_map(path):
    with open(path, "r") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        _fail("sizing map must be a JSON object")
    return data


def validate_map(sizing_map):
    if not sizing_map:
        _fail("sizing map is empty")

    devices = list(sizing_map.items())
    total_entries = 0
    seen_registers = set()

    for device_index, (device, bit_to_register) in enumerate(devices):
        if not isinstance(bit_to_register, dict):
            _fail("device '{}' must map to an object".format(device))

        expected_keys = {str(w) for w in BIT_WEIGHTS}
        actual_keys = set(bit_to_register.keys())
        missing = sorted(expected_keys - actual_keys)
        if missing:
            _fail("device '{}' missing required key '{}'".format(device, missing[0]))

        unexpected = sorted(actual_keys - expected_keys)
        if unexpected:
            _fail("device '{}' has unexpected key '{}'".format(device, unexpected[0]))

        for bit_index, bit_weight in enumerate(BIT_WEIGHTS):
            key = str(bit_weight)
            actual = _parse_int_register(bit_to_register[key], device, key)
            expected = _expected_register(device_index, bit_index)
            if actual != expected:
                _fail(
                    "mismatch at device '{}' bit '{}': expected {}, actual {}".format(
                        device, key, expected, actual
                    )
                )
            if actual in seen_registers:
                _fail("duplicate register detected: {}".format(actual))
            seen_registers.add(actual)
            total_entries += 1

    min_reg = min(seen_registers)
    max_reg = max(seen_registers)
    expected_count = len(devices) * BITS_PER_DEVICE
    if min_reg != BASE_REGISTER:
        _fail("unexpected minimum register: expected {}, actual {}".format(BASE_REGISTER, min_reg))
    if len(seen_registers) != expected_count:
        _fail(
            "unexpected unique register count: expected {}, actual {}".format(
                expected_count, len(seen_registers)
            )
        )
    if max_reg != BASE_REGISTER + expected_count - 1:
        _fail(
            "unexpected maximum register: expected {}, actual {}".format(
                BASE_REGISTER + expected_count - 1, max_reg
            )
        )

    return len(devices), total_entries, min_reg, max_reg


def main():
    parser = argparse.ArgumentParser(
        description="Validate equation-based reconstruction against device_name_to_sizing_registers.json"
    )
    parser.add_argument(
        "--map",
        dest="map_path",
        default=str(_default_map_path()),
        help="Path to device_name_to_sizing_registers.json",
    )
    args = parser.parse_args()

    sizing_map = _load_map(args.map_path)
    devices, entries, min_reg, max_reg = validate_map(sizing_map)
    print(
        "PASS: sizing equations identical to JSON map "
        "(devices={}, entries={}, range={}..{})".format(
            devices, entries, min_reg, max_reg
        )
    )


if __name__ == "__main__":
    try:
        main()
    except ValueError as exc:
        print("FAIL: {}".format(exc))
        raise SystemExit(1)
