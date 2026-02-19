# MOSbius V2 Register Map

This document describes the structure of `switch_matrix_register_map.json` and
the exact equations used to derive register addresses.

Validation status: the equations in this document are verified against
`switch_matrix_register_map.json` by `V2/validate_register_equations.py`.

## Overview

The switch matrix has:

- 96 rows total:
  - 92 numeric switch rows (`"1"` .. `"92"`)
  - 4 internal rows (`"internal_A"`, `"internal_B"`, `"internal_C"`, `"internal_D"`)
- 20 bus columns:
  - 12 SBUS columns: `SBUS1a..SBUS6b`
  - 8 RBUS columns: `RBUS1..RBUS8` (not present for internal rows)

The rows are organized in 4 banks, each with 24 slots:

- slots `1..23`: numeric switch rows
- slot `24`: internal row

Bank layout by equation index `s`:

- `s = 1..23` => bank 0 numeric rows
- `s = 24` => `internal_A`
- `s = 25..47` => bank 1 numeric rows
- `s = 48` => `internal_B`
- `s = 49..71` => bank 2 numeric rows
- `s = 72` => `internal_C`
- `s = 73..95` => bank 3 numeric rows
- `s = 96` => `internal_D`

## Derived Terms

Given row index `s` in `1..96`:

- `bank = (s - 1) // 24`  (0..3)
- `slot = ((s - 1) % 24) + 1`  (1..24)
- `idx = slot - 1`  (0..23)

For SBUS bus number `n` in `1..6` and phase in `{a, b}`:

- `phase = 0` for `a`
- `phase = 1` for `b`

For RBUS bus number `m` in `1..8`.

## Address Equations

### SBUS (all rows, including internal)

- `SBUSn a`:
  - `reg = 1 + 472*bank + 2*idx + 48*(n-1)`
- `SBUSn b`:
  - `reg = 2 + 472*bank + 2*idx + 48*(n-1)`

### RBUS (numeric rows only, `slot != 24`)

- `RBUSm`:
  - `reg = 289 + 472*bank + (slot-1) + 23*(m-1)`

Internal rows (`slot == 24`) do not have RBUS entries.

## Sizing Register Map

Sizing registers occupy a contiguous address range and are also derivable by
equation.

- Address range: `1889..2008`
- Devices: 24
- Bits per device: 5 (`0..31` sizing value)
- Bit weights: `1, 2, 4, 8, 16`

Let:

- `d` = device index in canonical sizing-device order (`0..23`)
- `w` = bit weight in `{1, 2, 4, 8, 16}`
- `b = log2(w)` (`0..4`)

Then the register address is:

- `reg = 1889 + 5*d + b`

Equivalent write rule for a size value `size` in `0..31`:

- for `b in [0..4]`:
  - `reg = 1889 + 5*d + b`
  - `value = 1 if ((size >> b) & 1) else 0`

The current canonical device order is the order in
`device_name_to_sizing_registers.json`:

1. `OTA_P`
2. `DCC1_P_L`
3. `DCC1_P_R`
4. `DCC2_P_L`
5. `DCC2_P_R`
6. `DCC3_P_L`
7. `DCC3_P_R`
8. `DCC4_P_L`
9. `DCC4_P_R`
10. `CC_N`
11. `CC_P`
12. `DINV1_L`
13. `DINV1_R`
14. `DINV2_L`
15. `DINV2_R`
16. `DCC1_N_L`
17. `DCC1_N_R`
18. `DCC2_N_L`
19. `DCC2_N_R`
20. `DCC3_N_L`
21. `DCC3_N_R`
22. `DCC4_N_L`
23. `DCC4_N_R`
24. `OTA_N`

## Practical Interpretation

- SBUS rows in each bank are densely patterned with:
  - row stride = 2
  - phase delta (`a -> b`) = +1
  - SBUS bus delta (`SBUSn -> SBUS(n+1)`) = +48
- RBUS rows in each bank are densely patterned with:
  - row stride = 1
  - RBUS bus delta (`RBUSm -> RBUS(m+1)`) = +23
- Bank-to-bank offset is `+472` for both SBUS and RBUS.

## Consolidating `chip_config_data`

Now that register addresses are derivable, `switch_matrix_register_map.json`
can be removed from runtime data and replaced by a compact equation-based
resolver.

Recommended consolidation:

1. Keep:
   - `pin_name_to_sw_matrix_pin_number.json`
   - a compact sizing-device order list (replace full sizing map JSON)
   - optional debug files:
     - `pin_name_to_number.json`
     - `pin_number_to_name.json`
2. Remove from runtime dependency:
   - `switch_matrix_register_map.json`
   - `device_name_to_sizing_registers.json`
3. Add code module:
   - `register_map_equations.py` with:
     - `sbus_register(sw_pin, sbus_name) -> int`
     - `rbus_register(sw_pin, rbus_name) -> int`
     - internal-row guard for RBUS
     - `size_register(device_index, bit_index) -> int`
4. Keep `V2/validate_register_equations.py` as a regression checker until
   equation migration is complete.

## Suggested Minimal Runtime Data Model

At runtime, route resolution only needs:

- pin terminal -> switch row key (`pin_name_to_sw_matrix_pin_number`)
- bus name (`SBUS*` / `RBUS*`)
- equation resolver

That avoids loading a 50KB+ register table JSON and reduces memory pressure on
MicroPython targets.
