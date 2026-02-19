import json


def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def write_bitstream_text(path, bitstream, order="asc", m2k=False):
    if order not in ("asc", "desc"):
        raise ValueError("order must be 'asc' or 'desc'")
    iterable = reversed(bitstream) if order == "desc" else bitstream
    with open(path, "w") as f:
        if m2k:
            f.write("0\n")
        for bit in iterable:
            f.write("{}\n".format(int(bit)))


def load_bitstream_text(path):
    bits = []
    with open(path, "r") as f:
        for line_no, raw_line in enumerate(f, 1):
            line = raw_line.strip()
            if not line:
                continue
            if line not in ("0", "1"):
                raise ValueError(
                    "Invalid bitstream value '{}' at line {} in {}".format(
                        line, line_no, path
                    )
                )
            bits.append(1 if line == "1" else 0)
    if not bits:
        raise ValueError("Bitstream file is empty: {}".format(path))
    return bits
