"""
Equation-based register address helpers for MOSbius V2.

This module computes:
- switch-matrix SBUS/RBUS register addresses
- sizing register addresses

It replaces large precomputed register map tables at runtime.
"""

INTERNAL_ROW_TO_INDEX = {
    "internal_A": 24,
    "internal_B": 48,
    "internal_C": 72,
    "internal_D": 96,
}

SIZING_DEVICE_ORDER = (
    "OTA_P",
    "DCC1_P_L",
    "DCC1_P_R",
    "DCC2_P_L",
    "DCC2_P_R",
    "DCC3_P_L",
    "DCC3_P_R",
    "DCC4_P_L",
    "DCC4_P_R",
    "CC_N",
    "CC_P",
    "DINV1_L",
    "DINV1_R",
    "DINV2_L",
    "DINV2_R",
    "DCC1_N_L",
    "DCC1_N_R",
    "DCC2_N_L",
    "DCC2_N_R",
    "DCC3_N_L",
    "DCC3_N_R",
    "DCC4_N_L",
    "DCC4_N_R",
    "OTA_N",
)

_SIZING_INDEX_BY_DEVICE = {name: i for i, name in enumerate(SIZING_DEVICE_ORDER)}


def _as_int(value, name):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError("{} must be an integer-like value, got {!r}".format(name, value))


def switch_equation_index(sw_pin):
    """
    Convert a switch-row key to equation index s (1..96).

    Supported inputs:
    - numeric switch rows: 1..92 (int or numeric str)
    - internal rows: "internal_A", "internal_B", "internal_C", "internal_D"
    """
    if isinstance(sw_pin, str) and sw_pin in INTERNAL_ROW_TO_INDEX:
        return INTERNAL_ROW_TO_INDEX[sw_pin]

    n = _as_int(sw_pin, "sw_pin")
    if not (1 <= n <= 92):
        raise ValueError("numeric sw_pin out of range 1..92: {}".format(n))

    # 23 numeric rows per bank, 24 slots per bank (slot 24 is internal).
    bank = (n - 1) // 23
    slot = ((n - 1) % 23) + 1
    return bank * 24 + slot


def _sbus_parts(sbus_name):
    if not isinstance(sbus_name, str):
        raise ValueError("sbus_name must be a string")
    if len(sbus_name) != 6 or not sbus_name.startswith("SBUS"):
        raise ValueError("invalid SBUS name '{}'; expected SBUS1a..SBUS6b".format(sbus_name))
    n = _as_int(sbus_name[4], "SBUS bus index")
    phase = sbus_name[5]
    if n < 1 or n > 6 or phase not in ("a", "b"):
        raise ValueError("invalid SBUS name '{}'; expected SBUS1a..SBUS6b".format(sbus_name))
    return n, phase


def _rbus_index(rbus_name):
    if not isinstance(rbus_name, str):
        raise ValueError("rbus_name must be a string")
    if len(rbus_name) != 5 or not rbus_name.startswith("RBUS"):
        raise ValueError("invalid RBUS name '{}'; expected RBUS1..RBUS8".format(rbus_name))
    m = _as_int(rbus_name[4], "RBUS bus index")
    if m < 1 or m > 8:
        raise ValueError("invalid RBUS name '{}'; expected RBUS1..RBUS8".format(rbus_name))
    return m


def sbus_register(sw_pin, sbus_name):
    """
    Return register address for SBUS bus at switch row.

    Formula:
      reg = 1 + 472*bank + 2*idx + 48*(n-1) + phase
    """
    s = switch_equation_index(sw_pin)
    n, phase_name = _sbus_parts(sbus_name)
    bank = (s - 1) // 24
    slot = ((s - 1) % 24) + 1
    idx = slot - 1
    phase = 0 if phase_name == "a" else 1
    return 1 + 472 * bank + 2 * idx + 48 * (n - 1) + phase


def rbus_register(sw_pin, rbus_name):
    """
    Return register address for RBUS bus at switch row.

    Formula (numeric rows only, no internal rows):
      reg = 289 + 472*bank + (slot-1) + 23*(m-1)
    """
    s = switch_equation_index(sw_pin)
    slot = ((s - 1) % 24) + 1
    if slot == 24:
        raise ValueError("RBUS is undefined for internal row '{}'".format(sw_pin))

    m = _rbus_index(rbus_name)
    bank = (s - 1) // 24
    return 289 + 472 * bank + (slot - 1) + 23 * (m - 1)


def switch_register(sw_pin, bus_name):
    """
    Convenience dispatcher for SBUS/RBUS names.
    """
    if isinstance(bus_name, str) and bus_name.startswith("SBUS"):
        return sbus_register(sw_pin, bus_name)
    if isinstance(bus_name, str) and bus_name.startswith("RBUS"):
        return rbus_register(sw_pin, bus_name)
    raise ValueError("unknown bus '{}'; expected SBUS* or RBUS*".format(bus_name))


def sizing_device_index(device_name):
    """
    Return canonical sizing device index (0..23).
    """
    if device_name not in _SIZING_INDEX_BY_DEVICE:
        raise ValueError("unknown sizing device '{}'".format(device_name))
    return _SIZING_INDEX_BY_DEVICE[device_name]


def sizing_register_by_index(device_index, bit_index):
    """
    Return sizing register from canonical indices.

    device_index: 0..23
    bit_index: 0..4, where 0/1/2/3/4 correspond to weights 1/2/4/8/16.
    """
    d = _as_int(device_index, "device_index")
    b = _as_int(bit_index, "bit_index")
    if not (0 <= d < len(SIZING_DEVICE_ORDER)):
        raise ValueError("device_index out of range 0..23: {}".format(d))
    if not (0 <= b <= 4):
        raise ValueError("bit_index out of range 0..4: {}".format(b))
    return 1889 + 5 * d + b


def sizing_register(device_name, bit_weight):
    """
    Return sizing register for device and bit weight.

    bit_weight must be one of: 1, 2, 4, 8, 16.
    """
    w = _as_int(bit_weight, "bit_weight")
    weight_to_bit_index = {1: 0, 2: 1, 4: 2, 8: 3, 16: 4}
    if w not in weight_to_bit_index:
        raise ValueError("bit_weight must be one of 1,2,4,8,16 (got {})".format(w))
    return sizing_register_by_index(sizing_device_index(device_name), weight_to_bit_index[w])


def sizing_registers_for_device(device_name):
    """
    Return {bit_weight: register} for a device.
    """
    return {w: sizing_register(device_name, w) for w in (1, 2, 4, 8, 16)}

