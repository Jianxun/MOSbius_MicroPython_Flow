# MOSbius V2 Tools

This folder contains host-side utilities (not required on Pico runtime).

## What Is Here

- `bitstream_generator.py`
  - Host CLI wrapper to generate bitstreams from config JSON.
  - Uses core logic from `V2/lib/`.
- `validate_register_equations.py`
  - Verifies switch-matrix equations match reference register map JSON.
- `validate_sizing_equations.py`
  - Verifies sizing equations match reference sizing register map JSON.
- `config_ref.json`
  - Reference config used for regression/golden checks.
- `bitstream.txt`
  - Reference/generated bitstream artifact.
- `chip_config_data/`
  - Reference data used for validation and documentation.

## Prerequisites

Run commands from the repository root:

```bash
cd /path/to/MOSbius_MicroPython_Flow
```

Use Python 3.

## Bitstream Generator

Generate from default runtime config (`V2/config.json`):

```bash
python3 V2/tools/bitstream_generator.py
```

Generate from a specific config:

```bash
python3 V2/tools/bitstream_generator.py V2/tools/config_ref.json /tmp/bitstream.txt --order asc
```

Generate descending order:

```bash
python3 V2/tools/bitstream_generator.py V2/tools/config_ref.json /tmp/bitstream_desc.txt --order desc
```

Generate M2K format (forces desc and prepends one leading `0`):

```bash
python3 V2/tools/bitstream_generator.py V2/tools/config_ref.json /tmp/bitstream_m2k.txt --m2k
```

Export CSV view:

```bash
python3 V2/tools/bitstream_generator.py V2/tools/config_ref.json /tmp/bitstream.txt --csv /tmp/bitstream.csv
```

## Equation Validators

Validate switch-matrix equation map:

```bash
python3 V2/tools/validate_register_equations.py
```

Validate sizing equation map:

```bash
python3 V2/tools/validate_sizing_equations.py
```

Both scripts support `--map` to validate an alternate JSON file:

```bash
python3 V2/tools/validate_register_equations.py --map /tmp/switch_matrix_register_map.json
python3 V2/tools/validate_sizing_equations.py --map /tmp/device_name_to_sizing_registers.json
```

## Golden Regression Example

```bash
python3 V2/tools/bitstream_generator.py V2/tools/config_ref.json /tmp/v2_ref.txt --order asc
python3 - <<'PY'
import hashlib
from pathlib import Path
print(hashlib.sha256(Path('/tmp/v2_ref.txt').read_bytes()).hexdigest())
PY
```

Expected SHA256:

`eea5637a6c5d81dfcee89d8e1eb2860abc38d59b850473bc2c122a8f9d9e6882`
