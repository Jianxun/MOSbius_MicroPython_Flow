# MOSbius MicroPython Flow

This repository contains two official MOSbius chip versions:

- `V1/`
- `V2/`

`V1` and `V2` are significantly different in architecture and features. Their software toolchains and config formats are incompatible.

In this repository, `V1/` and `V2/` are source folders only. On the Pico, copy one flow at a time to the Pico root (`/`) without keeping the `V1` or `V2` parent directory name.

## Repository Structure

- `V1/`
  - `main.py`: V1 entrypoint
  - `MOSbius.py`: V1 bitstream builder/programmer class
  - `connections.json`: V1 connection input
  - `README.md`: V1 usage details
- `V2/`
  - `main.py`: V2 runtime entrypoint (Pico + desktop-safe)
  - `config.json`: V2 runtime config
  - `lib/`: V2 runtime internals (driver, builder, validation, equations)
  - `tools/`: V2 host utilities (generator, loader, validators)
  - `README.md`: V2 runtime details
- `screenshots/`: setup and usage images

## Choose a Flow

1. Use `V1/` only with a `V1` chip and `V1` config/tooling.
2. Use `V2/` only with a `V2` chip and `V2` config/tooling.

## Quick Start

### V1

1. Read `V1/README.md`.
2. Copy `V1/MOSbius.py`, `V1/main.py`, and `V1/connections.json` to Pico root (`/`) as `MOSbius.py`, `main.py`, and `connections.json`.
3. Edit `V1/connections.json` and run `V1/main.py`.

### V2

1. Read `V2/README.md`.
2. Copy `V2/main.py`, `V2/config.json`, and `V2/lib/` to Pico root (`/`) as `main.py`, `config.json`, and `lib/`.
3. Edit `V2/main.py` (pins/timing/config path) and run it.
4. Optional host tools are under `V2/tools/`.

## Host-Side Validation (V2)

From the repository root:

```bash
python3 V2/tools/validate_register_equations.py
python3 V2/tools/validate_sizing_equations.py
```

## Notes

- Do not mix files, scripts, or config formats between `V1` and `V2`.
- Both flows can run on desktop Python for bitstream generation without GPIO programming.
