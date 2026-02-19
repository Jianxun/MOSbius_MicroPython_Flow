VALID_SBUS_MODES = ("ON", "OFF", "PHI1", "PHI2")


def parse_terminal_and_mode(value):
    if "@" not in value:
        return value, None, False
    terminal, mode = value.rsplit("@", 1)
    mode = mode.strip().upper()
    if mode not in VALID_SBUS_MODES:
        raise ValueError("SBUS: unknown suffix '{}' in '{}'".format(mode, value))
    return terminal, mode, True


def sbus_mode_to_pair(mode):
    mode = (mode or "OFF").upper()
    if mode == "ON":
        return 1, 1
    if mode == "PHI1":
        return 1, 0
    if mode == "PHI2":
        return 0, 1
    if mode == "OFF":
        return 0, 0
    raise ValueError("Invalid SBUS mode '{}'".format(mode))


def normalize_sbus_mode_for_csv(mode):
    mode = (mode or "OFF").upper()
    if mode == "PHI1":
        return "PH1"
    if mode == "PHI2":
        return "PH2"
    if mode in ("ON", "OFF"):
        return mode
    return "OFF"
