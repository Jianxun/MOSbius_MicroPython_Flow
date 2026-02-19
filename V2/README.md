# MOSbius V2 Runtime (RPi Pico)

This folder is organized so the Pico-facing workflow is simple:

- `V2/main.py` is the user entrypoint.
- `V2/config.json` is the selected circuit configuration.
- `V2/lib/` contains runtime driver/build/validation internals.

## Runtime Files To Copy To Pico

Copy these to the Pico filesystem:

- `V2/main.py`
- `V2/config.json` (or your own config file)
- `V2/lib/` (entire folder)

## User Configuration

Edit only `V2/main.py`:

- `PIN_EN`
- `PIN_CLK`
- `PIN_DATA`
- `T_CLK_HALF_CYCLE_US`
- `CONFIG_FILE` (relative to `main.py`, e.g. `config.json`, `configs/lab1.json`)

No other script edits are required for normal runtime use.

## Run Flow

When `main.py` runs:

1. Loads `CONFIG_FILE`
2. Validates config
3. Builds 2008-bit bitstream (ascending register order)
4. Programs MOSbius by shifting last bit first

## Notes

- The runtime validates config and fails fast on invalid buses/pins/sizing.
- On desktop Python, `main.py` generates the bitstream but skips GPIO programming.
- Optional loader for prebuilt bitstreams lives in `V2/tools/bitstream_loader.py` (host/tool helper, not runtime).
