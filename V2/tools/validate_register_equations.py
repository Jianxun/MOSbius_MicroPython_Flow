import argparse
import json
from pathlib import Path


SBUS_KEYS = [f"SBUS{n}{phase}" for n in range(1, 7) for phase in ("a", "b")]
RBUS_KEYS = [f"RBUS{n}" for n in range(1, 9)]
INTERNAL_NAMES = {"internal_A", "internal_B", "internal_C", "internal_D"}


def _default_map_path():
    return Path(__file__).resolve().parent / "chip_config_data" / "switch_matrix_register_map.json"


def _fail(message):
    raise ValueError(message)


def _parse_int_register(raw_value, row_key, bus_key):
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        _fail(
            "non-integer register value at row '{}' bus '{}': {!r}".format(
                row_key, bus_key, raw_value
            )
        )


def _expected_sbus_register(s, bus_name):
    bank = (s - 1) // 24
    slot = ((s - 1) % 24) + 1
    idx = slot - 1
    n = int(bus_name[4])
    phase = 0 if bus_name.endswith("a") else 1
    return 1 + 472 * bank + 2 * idx + 48 * (n - 1) + phase


def _expected_rbus_register(s, bus_name):
    bank = (s - 1) // 24
    slot = ((s - 1) % 24) + 1
    m = int(bus_name[4])
    return 289 + 472 * bank + (slot - 1) + 23 * (m - 1)


def _load_map(path):
    with open(path, "r") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        _fail("register map must be a JSON object")
    return data


def _canonical_order(register_map):
    ordered = []
    for row_key, row_data in register_map.items():
        if not isinstance(row_data, dict):
            _fail("row '{}' must be a JSON object".format(row_key))
        if "SBUS1a" not in row_data:
            _fail("row '{}' is missing required key 'SBUS1a'".format(row_key))
        sbus1a = _parse_int_register(row_data["SBUS1a"], row_key, "SBUS1a")
        ordered.append((sbus1a, row_key, row_data))
    ordered.sort(key=lambda x: x[0])
    return ordered


def _validate_row_keys(row_key, row_data, expected_buses):
    actual_bus_keys = {k for k in row_data.keys() if k != "display_name"}
    missing = sorted(expected_buses - actual_bus_keys)
    if missing:
        _fail("row '{}' missing required key '{}'".format(row_key, missing[0]))

    unexpected = sorted(actual_bus_keys - expected_buses)
    if unexpected:
        _fail("row '{}' has unexpected key '{}'".format(row_key, unexpected[0]))


def validate_map(register_map):
    ordered_rows = _canonical_order(register_map)
    if len(ordered_rows) != 96:
        _fail("expected 96 rows, got {}".format(len(ordered_rows)))

    total_bus_entries = 0
    seen_internal_names = set()

    for s, (_, row_key, row_data) in enumerate(ordered_rows, 1):
        slot = ((s - 1) % 24) + 1
        has_rbus1 = "RBUS1" in row_data

        if slot == 24:
            if has_rbus1:
                _fail("internal row '{}' should not contain RBUS keys".format(row_key))
            if row_key not in INTERNAL_NAMES:
                _fail(
                    "row '{}' at internal slot {} is not a recognized internal row".format(
                        row_key, s
                    )
                )
            seen_internal_names.add(row_key)
            expected_buses = set(SBUS_KEYS)
        else:
            if not has_rbus1:
                _fail("numeric row '{}' missing RBUS keys (RBUS1 absent)".format(row_key))
            if row_key in INTERNAL_NAMES:
                _fail("row '{}' is internal but appears in numeric slot".format(row_key))
            expected_buses = set(SBUS_KEYS + RBUS_KEYS)

        _validate_row_keys(row_key, row_data, expected_buses)

        for bus_key in SBUS_KEYS:
            actual = _parse_int_register(row_data[bus_key], row_key, bus_key)
            expected = _expected_sbus_register(s, bus_key)
            if actual != expected:
                _fail(
                    "mismatch at row '{}' bus '{}': expected {}, actual {}".format(
                        row_key, bus_key, expected, actual
                    )
                )
            total_bus_entries += 1

        if slot != 24:
            for bus_key in RBUS_KEYS:
                actual = _parse_int_register(row_data[bus_key], row_key, bus_key)
                expected = _expected_rbus_register(s, bus_key)
                if actual != expected:
                    _fail(
                        "mismatch at row '{}' bus '{}': expected {}, actual {}".format(
                            row_key, bus_key, expected, actual
                        )
                    )
                total_bus_entries += 1

    if seen_internal_names != INTERNAL_NAMES:
        missing = sorted(INTERNAL_NAMES - seen_internal_names)
        _fail("missing internal rows: {}".format(", ".join(missing)))

    return len(ordered_rows), total_bus_entries


def main():
    parser = argparse.ArgumentParser(
        description="Validate equation-based reconstruction against switch_matrix_register_map.json"
    )
    parser.add_argument(
        "--map",
        dest="map_path",
        default=str(_default_map_path()),
        help="Path to switch_matrix_register_map.json",
    )
    args = parser.parse_args()

    register_map = _load_map(args.map_path)
    rows, bus_entries = validate_map(register_map)
    print(
        "PASS: equations identical to JSON map (rows={}, bus_entries={})".format(
            rows, bus_entries
        )
    )


if __name__ == "__main__":
    try:
        main()
    except ValueError as exc:
        print("FAIL: {}".format(exc))
        raise SystemExit(1)
