import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LIB_DIR = os.path.join(os.path.dirname(BASE_DIR), "lib")
sys.path.insert(0, LIB_DIR)

from bitstream_builder import build_bitstream
from config_io import load_json, write_bitstream_text
from config_validation import validate_and_normalize_config
from connection_semantics import normalize_sbus_mode_for_csv


def _bus_sort_key(bus):
    if bus.startswith("RBUS"):
        prefix = "RBUS"
        rest = bus[len("RBUS") :]
    elif bus.startswith("SBUS"):
        prefix = "SBUS"
        rest = bus[len("SBUS") :]
    else:
        prefix = bus
        rest = ""
    suffix = ""
    if rest and rest[-1] in ("a", "b"):
        suffix = rest[-1]
        rest = rest[:-1]
    try:
        number = int(rest) if rest else 0
    except ValueError:
        number = 0
    return (prefix, number, suffix, bus)


def _build_csv_table(connections, pin_name_to_number):
    buses = sorted(connections.keys(), key=_bus_sort_key)
    rbus_pins = {}
    sbus_modes = {}
    pins = set()

    for bus, entries in connections.items():
        if bus.startswith("RBUS"):
            rbus_pins[bus] = set(entries)
            pins.update(entries)
            continue

        if not bus.startswith("SBUS"):
            continue

        sbus_modes[bus] = {}
        for entry in entries:
            terminal = entry["terminal"]
            connection = entry["connection"]
            pins.add(terminal)
            sbus_modes[bus][terminal] = normalize_sbus_mode_for_csv(connection)

    def _pin_sort_key(pin_name):
        pin_num = pin_name_to_number.get(pin_name)
        try:
            return int(pin_num)
        except (TypeError, ValueError):
            return 10**9

    rows = []
    for pin in sorted(pins, key=_pin_sort_key):
        pin_num = pin_name_to_number.get(pin)
        if pin_num is None:
            raise ValueError("CSV: pin '{}' not found in pin_name_to_number mapping".format(pin))
        row_label = "{}:{}".format(int(pin_num), pin)
        row = [row_label]
        for bus in buses:
            if bus.startswith("RBUS"):
                value = 1 if pin in rbus_pins.get(bus, set()) else 0
                row.append(str(value))
            elif bus.startswith("SBUS"):
                row.append(sbus_modes.get(bus, {}).get(pin, "OFF"))
            else:
                row.append("")
        rows.append(row)

    return ["pin"] + buses, rows


def _write_csv(output_path, header, rows):
    with open(output_path, "w") as f:
        f.write(",".join(header) + "\n")
        for row in rows:
            f.write(",".join(row) + "\n")


def _usage():
    script = os.path.basename(sys.argv[0])
    return (
        "Usage: {} [config.json] [output.txt] [--order asc|desc] [--csv path] [--m2k]\\n".format(script)
        + "Defaults: config.json in script folder, output=bitstream.txt, order=asc\\n"
    )


def _parse_args(argv, default_config, default_output):
    config_path = default_config
    output_path = default_output
    order = "asc"
    csv_path = None
    m2k = False
    positionals = []
    i = 1
    while i < len(argv):
        arg = argv[i]
        if arg in ("-h", "--help"):
            print(_usage())
            raise SystemExit(0)
        if arg.startswith("--order="):
            order = arg.split("=", 1)[1].strip().lower()
        elif arg == "--order":
            if i + 1 >= len(argv):
                raise ValueError("Missing value for --order")
            order = argv[i + 1].strip().lower()
            i += 1
        elif arg.startswith("--csv="):
            csv_path = arg.split("=", 1)[1].strip()
        elif arg == "--csv":
            if i + 1 >= len(argv):
                raise ValueError("Missing value for --csv")
            csv_path = argv[i + 1].strip()
            i += 1
        elif arg == "--m2k":
            m2k = True
        else:
            positionals.append(arg)
        i += 1

    if len(positionals) >= 1:
        config_path = positionals[0]
    if len(positionals) >= 2:
        output_path = positionals[1]
    if len(positionals) > 2:
        raise ValueError("Too many positional arguments")
    if order not in ("asc", "desc"):
        raise ValueError("Order must be 'asc' or 'desc'")
    if m2k:
        order = "desc"
    return config_path, output_path, order, csv_path, m2k


def main():
    base_dir = BASE_DIR
    default_config = os.path.join(os.path.dirname(base_dir), "config.json")
    default_output = os.path.join(base_dir, "bitstream.txt")
    config_path, output_path, order, csv_path, m2k = _parse_args(sys.argv, default_config, default_output)

    mapping_dir = os.path.join(base_dir, "chip_config_data")
    runtime_mapping_dir = os.path.join(LIB_DIR, "chip_config_data")
    pin_map_path = os.path.join(runtime_mapping_dir, "pin_name_to_sw_matrix_pin_number.json")
    pin_name_to_number_path = os.path.join(mapping_dir, "pin_name_to_number.json")

    config = load_json(config_path)
    pin_to_sw_matrix = load_json(pin_map_path)
    normalized = validate_and_normalize_config(config, pin_to_sw_matrix)

    bitstream = build_bitstream(
        normalized["connections"],
        normalized["sizes"],
        pin_to_sw_matrix,
        track_sources=True,
    )

    write_bitstream_text(output_path, bitstream, order=order, m2k=m2k)
    extra_rows = 1 if m2k else 0
    print("Bitstream saved to {} ({} bits, order={})".format(output_path, len(bitstream) + extra_rows, order))

    if csv_path:
        pin_name_to_number = load_json(pin_name_to_number_path)
        header, rows = _build_csv_table(normalized["connections"], pin_name_to_number)
        _write_csv(csv_path, header, rows)
        print("CSV saved to {} ({} rows)".format(csv_path, len(rows)))


if __name__ == "__main__":
    main()
