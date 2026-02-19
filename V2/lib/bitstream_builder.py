import register_map_equations as reg_eq
from connection_semantics import sbus_mode_to_pair
from settings import EXPECTED_BITS


def _set_bit(bitstream, register, value, source, set_sources):
    if register < 1 or register > EXPECTED_BITS:
        raise ValueError("{}: register {} out of range 1..{}".format(source, register, EXPECTED_BITS))
    index = register - 1
    current = bitstream[index]
    if set_sources[index] is not None and current != value:
        raise ValueError(
            "{}: conflicting write for register {} ({} -> {}, previous source: {})".format(
                source, register, current, value, set_sources[index]
            )
        )
    bitstream[index] = value
    set_sources[index] = source


def build_bitstream(connections, sizes, pin_to_sw_matrix):
    bitstream = bytearray(EXPECTED_BITS)
    set_sources = [None] * EXPECTED_BITS

    for bus, entries in connections.items():
        if bus.startswith("RBUS"):
            for terminal in entries:
                sw_pin = pin_to_sw_matrix[terminal]
                register = reg_eq.rbus_register(sw_pin, bus)
                _set_bit(bitstream, register, 1, "RBUS {} {}".format(bus, terminal), set_sources)
            continue

        if bus.startswith("SBUS"):
            has_suffix = bus[-1:] in ("a", "b")
            for entry in entries:
                terminal = entry["terminal"]
                connection = entry["connection"]
                sw_pin = pin_to_sw_matrix[terminal]

                if has_suffix:
                    register = reg_eq.sbus_register(sw_pin, bus)
                    a, b = sbus_mode_to_pair(connection)
                    value = a if bus.endswith("a") else b
                    _set_bit(
                        bitstream,
                        register,
                        value,
                        "SBUS {} {} {}".format(bus, terminal, connection),
                        set_sources,
                    )
                    continue

                reg_a = reg_eq.sbus_register(sw_pin, "{}a".format(bus))
                reg_b = reg_eq.sbus_register(sw_pin, "{}b".format(bus))
                a, b = sbus_mode_to_pair(connection)
                _set_bit(
                    bitstream,
                    reg_a,
                    a,
                    "SBUS {}a {} {}".format(bus, terminal, connection),
                    set_sources,
                )
                _set_bit(
                    bitstream,
                    reg_b,
                    b,
                    "SBUS {}b {} {}".format(bus, terminal, connection),
                    set_sources,
                )
            continue

        raise ValueError("Unknown bus '{}'".format(bus))

    for device, size in sizes.items():
        for bit_weight in (1, 2, 4, 8, 16):
            register = reg_eq.sizing_register(device, bit_weight)
            value = 1 if (size & bit_weight) else 0
            _set_bit(
                bitstream,
                register,
                value,
                "sizes {} bit {}".format(device, bit_weight),
                set_sources,
            )

    return bitstream
