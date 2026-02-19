import json
import os
import sys

MAX_REGISTER = 2008


def _load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def _warn(message):
    print(f"Warning: {message}")


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


def _parse_terminal_and_mode(value):
    if "@" not in value:
        return value, None, False
    terminal, mode = value.rsplit("@", 1)
    mode = mode.strip().upper()
    if mode not in ("ON", "OFF", "PHI1", "PHI2"):
        _warn(f"SBUS: unknown suffix '{mode}' in '{value}', defaulting to ON")
        return terminal, "ON", True
    return terminal, mode, True


def _set_bit(bitstream, register, value, source, set_sources):
    if register < 1 or register > MAX_REGISTER:
        _warn(f"{source}: register {register} out of range 1..{MAX_REGISTER}")
        return
    index = register - 1
    current = bitstream[index]
    if set_sources[index] is not None and current != value:
        _warn(
            f"{source}: overwriting register {register} from {current} to {value} "
            f"(previously set by {set_sources[index]})"
        )
    bitstream[index] = value
    set_sources[index] = source


def _normalize_sbus_mode(mode):
    mode = (mode or "OFF").upper()
    if mode == "PHI1":
        return "PH1"
    if mode == "PHI2":
        return "PH2"
    if mode in ("ON", "OFF"):
        return mode
    return "OFF"


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

        has_suffix = bus[-1:] in ("a", "b")
        sbus_modes[bus] = {}
        for entry in entries:
            if isinstance(entry, str):
                terminal, parsed_mode, _ = _parse_terminal_and_mode(entry)
                connection = parsed_mode or "ON"
            elif isinstance(entry, dict):
                terminal = entry.get("terminal")
                connection = entry.get("connection", "OFF")
                if terminal is None:
                    continue
                terminal, parsed_mode, had_suffix = _parse_terminal_and_mode(terminal)
                if had_suffix:
                    connection = parsed_mode
            else:
                continue

            pins.add(terminal)
            if has_suffix:
                sbus_modes[bus][terminal] = _normalize_sbus_mode(connection)
            else:
                sbus_modes[bus][terminal] = _normalize_sbus_mode(connection)

    rows = []
    def _pin_sort_key(pin_name):
        pin_num = pin_name_to_number.get(pin_name)
        try:
            return int(pin_num)
        except (TypeError, ValueError):
            return 10**9

    for pin in sorted(pins, key=_pin_sort_key):
        pin_num = pin_name_to_number.get(pin)
        if pin_num is None:
            _warn(f"CSV: pin '{pin}' not found in pin_name_to_number mapping")
            continue
        row_label = f"{int(pin_num)}:{pin}"
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

    header = ["pin"] + buses
    return header, rows


def _write_csv(output_path, header, rows):
    with open(output_path, "w") as f:
        f.write(",".join(header) + "\n")
        for row in rows:
            f.write(",".join(row) + "\n")


def _apply_connections(bitstream, connections, pin_to_sw_matrix, sw_matrix_to_register, set_sources):
    for bus, entries in connections.items():
        if bus.startswith("RBUS"):
            for pin in entries:
                sw_matrix_pin = pin_to_sw_matrix.get(pin)
                if sw_matrix_pin is None:
                    _warn(f"RBUS: pin '{pin}' not found in pin-to-switch map")
                    continue
                if not isinstance(sw_matrix_pin, str):
                    sw_matrix_pin = str(int(sw_matrix_pin))
                register = sw_matrix_to_register.get(sw_matrix_pin, {}).get(bus)
                if register is None:
                    _warn(f"RBUS: register not found for sw_pin '{sw_matrix_pin}' bus '{bus}'")
                    continue
                _set_bit(bitstream, int(register), 1, f"RBUS {bus} pin {pin}", set_sources)
        elif bus.startswith("SBUS"):
            has_suffix = bus[-1:] in ("a", "b")
            for entry in entries:
                if isinstance(entry, str):
                    terminal, parsed_mode, _ = _parse_terminal_and_mode(entry)
                    connection = parsed_mode or "ON"
                elif isinstance(entry, dict):
                    terminal = entry.get("terminal")
                    connection = entry.get("connection", "OFF")
                    if terminal is None:
                        _warn(f"SBUS: missing terminal in {entry}")
                        continue
                    terminal, parsed_mode, had_suffix = _parse_terminal_and_mode(terminal)
                    if had_suffix:
                        if "connection" in entry and connection != parsed_mode:
                            _warn(
                                f"SBUS: terminal suffix overrides connection "
                                f"({connection} -> {parsed_mode}) for '{terminal}'"
                            )
                        connection = parsed_mode
                else:
                    _warn(f"SBUS: invalid entry type {type(entry).__name__}: {entry}")
                    continue

                sw_matrix_pin = pin_to_sw_matrix.get(terminal)
                if sw_matrix_pin is None:
                    _warn(f"SBUS: terminal '{terminal}' not found in pin-to-switch map")
                    continue
                if not isinstance(sw_matrix_pin, str):
                    sw_matrix_pin = str(int(sw_matrix_pin))

                if has_suffix:
                    register = sw_matrix_to_register.get(sw_matrix_pin, {}).get(bus)
                    if register is None:
                        _warn(f"SBUS: register not found for sw_pin '{sw_matrix_pin}' bus '{bus}'")
                        continue
                    if connection in ("ON", "OFF"):
                        value = 1 if connection == "ON" else 0
                    elif connection == "PHI1":
                        value = 1 if bus.endswith("a") else 0
                    elif connection == "PHI2":
                        value = 0 if bus.endswith("a") else 1
                    else:
                        value = 0
                    _set_bit(
                        bitstream,
                        int(register),
                        value,
                        f"SBUS {bus} {terminal} {connection}",
                        set_sources,
                    )
                    continue

                sbus_a = f"{bus}a"
                sbus_b = f"{bus}b"
                register_a = sw_matrix_to_register.get(sw_matrix_pin, {}).get(sbus_a)
                register_b = sw_matrix_to_register.get(sw_matrix_pin, {}).get(sbus_b)
                if register_a is None or register_b is None:
                    _warn(f"SBUS: register not found for sw_pin '{sw_matrix_pin}' buses '{sbus_a}/{sbus_b}'")
                    continue

                if connection == "ON":
                    a_value, b_value = 1, 1
                elif connection == "PHI1":
                    a_value, b_value = 1, 0
                elif connection == "PHI2":
                    a_value, b_value = 0, 1
                else:
                    a_value, b_value = 0, 0

                _set_bit(
                    bitstream,
                    int(register_a),
                    a_value,
                    f"SBUS {bus} {terminal} {connection}",
                    set_sources,
                )
                _set_bit(
                    bitstream,
                    int(register_b),
                    b_value,
                    f"SBUS {bus} {terminal} {connection}",
                    set_sources,
                )
        else:
            _warn(f"Unknown bus '{bus}' (expected RBUS/SBUS)")


def _apply_sizes(bitstream, sizes, device_to_registers, set_sources):
    for device, bit_to_register in device_to_registers.items():
        size = sizes.get(device, [0])[0]
        if not (0 <= size <= 31):
            _warn(f"size {size} for device {device} is not 5-bit; defaulting to 0")
            size = 0
        for bit, register in sorted(bit_to_register.items(), key=lambda x: int(x[0])):
            value = 1 if int(bit) & size else 0
            _set_bit(bitstream, int(register), value, f"sizes {device} bit {bit}", set_sources)


def _write_bitstream(bitstream, output_path, order, m2k):
    if order == "desc":
        iterable = reversed(bitstream)
    else:
        iterable = bitstream
    with open(output_path, "w") as f:
        if m2k:
            f.write("0\n")
        for bit in iterable:
            f.write(f"{bit}\n")


def _usage():
    script = os.path.basename(sys.argv[0])
    return (
        f"Usage: {script} [config.json] [output.txt] [--order asc|desc] [--csv path] [--m2k]\\n"
        f"Defaults: config.json in script folder, output=bitstream.txt, order=asc\\n"
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
    base_dir = os.path.dirname(os.path.abspath(__file__))
    default_config = os.path.join(base_dir, "config.json")
    default_output = os.path.join(base_dir, "bitstream.txt")
    config_path, output_path, order, csv_path, m2k = _parse_args(sys.argv, default_config, default_output)

    mapping_dir = os.path.join(base_dir, "chip_config_data")
    pin_map_path = os.path.join(mapping_dir, "pin_name_to_sw_matrix_pin_number.json")
    register_map_path = os.path.join(mapping_dir, "switch_matrix_register_map.json")
    sizes_map_path = os.path.join(mapping_dir, "device_name_to_sizing_registers.json")

    config = _load_json(config_path)
    connections = config.get("connections", config if isinstance(config, dict) else {})
    sizes = config.get("sizes", {})

    pin_to_sw_matrix = _load_json(pin_map_path)
    sw_matrix_to_register = _load_json(register_map_path)
    device_to_registers = _load_json(sizes_map_path)
    pin_name_to_number_path = os.path.join(mapping_dir, "pin_name_to_number.json")
    pin_name_to_number = _load_json(pin_name_to_number_path)

    bitstream = [0] * MAX_REGISTER
    set_sources = [None] * MAX_REGISTER
    if connections:
        _apply_connections(bitstream, connections, pin_to_sw_matrix, sw_matrix_to_register, set_sources)
    if sizes:
        _apply_sizes(bitstream, sizes, device_to_registers, set_sources)

    _write_bitstream(bitstream, output_path, order, m2k)
    extra_rows = 1 if m2k else 0
    print(
        f"Bitstream saved to {output_path} ({len(bitstream) + extra_rows} bits, order={order})"
    )

    if csv_path:
        header, rows = _build_csv_table(connections, pin_name_to_number)
        _write_csv(csv_path, header, rows)
        print(f"CSV saved to {csv_path} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
