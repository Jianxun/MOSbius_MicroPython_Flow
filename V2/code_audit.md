# V2 Runtime Audit and Handoff

## Context Snapshot

- Date: 2026-02-19
- Branch: `feature/v2-experiments`
- Recent commits:
  - `5061dc4` Split V2 runtime and tools; add usage docs
  - `451e238` Reorganize V2 with root-only main and config
  - `f0f681b` Encapsulate runtime flow in V2 driver
  - `b057822` Refactor V2 into shared builder, validation, and Pico main flow
  - `87eedd1` Refactor V2 generator to use register equations
  - `a0218da` Add V2 register-map equations and validators

## Status Update (2026-02-19)

Completed cleanup:

- Pin defaults removed from `V2/lib/settings.py`; runtime pin/timing edits live in `V2/main.py`.
- `V2/lib/bitstream_loader.py` moved to `V2/tools/bitstream_loader.py`.
- `V2/lib/driver.py` config path now supports absolute paths and resolves relative paths against the runtime root (directory containing `main.py` and `lib/`).
- Removed dead helpers:
  - `MOSbiusV2Driver.default_config_path()`
  - `config_io.default_path_near_module()`
- Added optional low-memory build mode:
  - `build_bitstream(..., track_sources=False)` by default.
  - Runtime driver uses `track_sources=False`.
  - Host generator uses `track_sources=True`.

## Current Runtime Layout

- User-facing runtime entrypoint:
  - `V2/main.py`
- User-facing runtime config:
  - `V2/config.json`
- Runtime internals:
  - `V2/lib/driver.py`
  - `V2/lib/bitstream_builder.py`
  - `V2/lib/config_validation.py`
  - `V2/lib/config_io.py`
  - `V2/lib/connection_semantics.py`
  - `V2/lib/programmer.py`
  - `V2/lib/register_map_equations.py`
  - `V2/lib/settings.py`
  - `V2/lib/chip_config_data/pin_name_to_sw_matrix_pin_number.json`

- Host/tools are separated under:
  - `V2/tools/*`
  - includes `V2/tools/bitstream_loader.py`

## Confirmed Runtime Behavior

- `main.py` settings are user-editable:
  - `PIN_EN`, `PIN_CLK`, `PIN_DATA`
  - `T_CLK_HALF_CYCLE_US`
  - `CONFIG_FILE` (relative to `V2/main.py`)
- Driver builds ascending-order bitstream and programs with reversed shift order (last bit first).
- Equation-based register mapping is in place and validated.

## Audit Findings (ordered by impact)

1. Pin/timing source is split and can drift
- `V2/main.py` defines user pins/timing.
- `V2/lib/settings.py` still defines another set.
- `V2/lib/bitstream_loader.py` uses `settings` pins, not `main.py` pins.
- Risk: loader can program different GPIOs than runtime main flow.

2. Runtime still includes dead/legacy API surface
- `V2/lib/driver.py`: `default_config_path()` no longer needed under `CONFIG_FILE` model.
- `V2/lib/config_io.py`: `default_path_near_module()` appears unused.
- `V2/lib/register_map_equations.py`: some convenience helpers unused in runtime path.
- Impact: extra noise and maintenance overhead on Pico.

3. `bitstream_loader.py` conflicts with the "main.py is only user-config surface" goal
- Loader has its own pin/timing defaults and CLI-style behavior.
- This breaks UX consistency.

4. Driver config path semantics are permissive but unclear
- `driver` currently resolves config by joining project dir with provided value.
- Works for relative path policy, but absolute-path behavior is not explicit.

5. Optional RAM reduction opportunity in runtime builder
- `V2/lib/bitstream_builder.py` allocates `set_sources = [None] * 2008` for conflict tracing.
- Useful for debug; can be made optional for lower runtime RAM footprint.

## Recommended Cleanup Plan (next session)

1. Make `main.py` the single source of runtime pin/timing truth
- Remove pin/timing defaults from `V2/lib/settings.py`.
- Ensure all runtime programming paths take pin/timing from caller.

2. Decide loader role explicitly
- Either remove `V2/lib/bitstream_loader.py` from runtime set, or
- keep it as pure helper without its own pin/timing defaults.

3. Trim unused runtime symbols
- Remove or move unused helpers from runtime modules (into tools if needed).

4. Harden config path behavior in driver
- Explicitly support:
  - relative paths resolved against `V2/`
  - absolute paths used as-is

5. Add optional low-memory mode in builder
- `build_bitstream(..., track_sources=False)` for runtime.
- `track_sources=True` for debug/host tools.

## Suggested Acceptance Criteria for Cleanup

- Runtime user edits only `V2/main.py` and `V2/config.json`.
- No duplicate pin/timing defaults anywhere in `V2/lib`.
- `main.py` works unchanged on Pico and desktop.
- Host tools under `V2/tools` still work.
- Golden checksum workflow remains unchanged.

## Notes for Resuming

- Keep runtime/tool separation intact:
  - runtime: `V2/main.py`, `V2/config.json`, `V2/lib/*`
  - tools: `V2/tools/*`
- Preserve existing bitstream semantics:
  - generate ascending register order
  - shift reversed during programming
- Avoid changing equation math without rerunning validators:
  - `V2/tools/validate_register_equations.py`
  - `V2/tools/validate_sizing_equations.py`
