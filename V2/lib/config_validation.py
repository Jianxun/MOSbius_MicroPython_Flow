import register_map_equations as reg_eq

VALID_SBUS_MODES = ("ON", "OFF", "PHI1", "PHI2")


def _parse_terminal_and_mode(value):
    if "@" not in value:
        return value, None, False
    terminal, mode = value.rsplit("@", 1)
    mode = mode.strip().upper()
    if mode not in VALID_SBUS_MODES:
        raise ValueError("SBUS: unknown suffix '{}' in '{}'".format(mode, value))
    return terminal, mode, True


def _normalize_size_value(device, raw):
    if isinstance(raw, list):
        if len(raw) != 1:
            raise ValueError(
                "sizes.{} must be integer or one-item list, got {} items".format(
                    device, len(raw)
                )
            )
        raw = raw[0]
    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise ValueError("sizes.{} must be an integer-like value".format(device))
    if not (0 <= value <= 31):
        raise ValueError("sizes.{}={} out of range 0..31".format(device, value))
    return value


def _parse_sbus_entry(entry, path):
    if isinstance(entry, str):
        terminal, parsed_mode, _ = _parse_terminal_and_mode(entry)
        return {"terminal": terminal, "connection": parsed_mode or "ON"}

    if isinstance(entry, dict):
        terminal = entry.get("terminal")
        if terminal is None:
            raise ValueError("{} missing required field 'terminal'".format(path))
        terminal, parsed_mode, had_suffix = _parse_terminal_and_mode(terminal)
        connection = entry.get("connection", "OFF")
        connection = str(connection).upper()
        if had_suffix:
            connection = parsed_mode
        if connection not in VALID_SBUS_MODES:
            raise ValueError(
                "{} has invalid connection '{}'; expected ON/OFF/PHI1/PHI2".format(
                    path, connection
                )
            )
        return {"terminal": terminal, "connection": connection}

    raise ValueError("{} invalid entry type {}".format(path, type(entry).__name__))


def validate_and_normalize_config(config, pin_to_sw_matrix):
    if not isinstance(config, dict):
        raise ValueError("config must be a JSON object")

    raw_connections = config.get("connections", config if isinstance(config, dict) else {})
    raw_sizes = config.get("sizes", {})

    if not isinstance(raw_connections, dict):
        raise ValueError("connections must be a JSON object")
    if not isinstance(raw_sizes, dict):
        raise ValueError("sizes must be a JSON object")

    normalized_connections = {}
    for bus, entries in raw_connections.items():
        if not isinstance(bus, str):
            raise ValueError("connections keys must be strings")
        if not isinstance(entries, list):
            raise ValueError("connections.{} must be a list".format(bus))

        if bus.startswith("RBUS"):
            if bus not in ("RBUS1", "RBUS2", "RBUS3", "RBUS4", "RBUS5", "RBUS6", "RBUS7", "RBUS8"):
                raise ValueError("unknown RBUS '{}'".format(bus))
            pin_list = []
            for i, terminal in enumerate(entries):
                if not isinstance(terminal, str):
                    raise ValueError("connections.{}[{}] must be string terminal".format(bus, i))
                if terminal not in pin_to_sw_matrix:
                    raise ValueError("connections.{}[{}] unknown terminal '{}'".format(bus, i, terminal))
                pin_list.append(terminal)
            normalized_connections[bus] = pin_list
            continue

        if bus.startswith("SBUS"):
            if bus[-1:] in ("a", "b"):
                base = bus[:-1]
                if base not in ("SBUS1", "SBUS2", "SBUS3", "SBUS4", "SBUS5", "SBUS6"):
                    raise ValueError("unknown SBUS '{}'".format(bus))
            elif bus not in ("SBUS1", "SBUS2", "SBUS3", "SBUS4", "SBUS5", "SBUS6"):
                raise ValueError("unknown SBUS '{}'".format(bus))

            out_entries = []
            for i, entry in enumerate(entries):
                parsed = _parse_sbus_entry(entry, "connections.{}[{}]".format(bus, i))
                terminal = parsed["terminal"]
                if terminal not in pin_to_sw_matrix:
                    raise ValueError(
                        "connections.{}[{}] unknown terminal '{}'".format(bus, i, terminal)
                    )
                out_entries.append(parsed)
            normalized_connections[bus] = out_entries
            continue

        raise ValueError("unknown bus '{}' (expected RBUS*/SBUS*)".format(bus))

    known_devices = set(reg_eq.SIZING_DEVICE_ORDER)
    unknown_devices = sorted(set(raw_sizes.keys()) - known_devices)
    if unknown_devices:
        raise ValueError("unknown sizing device '{}'".format(unknown_devices[0]))

    normalized_sizes = {}
    for device in reg_eq.SIZING_DEVICE_ORDER:
        raw = raw_sizes.get(device, 0)
        normalized_sizes[device] = _normalize_size_value(device, raw)

    return {"connections": normalized_connections, "sizes": normalized_sizes}
