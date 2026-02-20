#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

usage() {
  cat <<'EOF'
Usage:
  scripts/upload_runtime.sh v1 [--port PORT] [--clean]
  scripts/upload_runtime.sh v2 [--port PORT] [--clean]

Examples:
  scripts/upload_runtime.sh v1
  scripts/upload_runtime.sh v2 --port /dev/tty.usbmodem1101
  scripts/upload_runtime.sh v2 --clean

Notes:
  - Requires mpremote: https://docs.micropython.org/en/latest/reference/mpremote.html
  - Upload target is Pico root (/), with no V1/V2 parent directory.
EOF
}

if ! command -v mpremote >/dev/null 2>&1; then
  echo "Error: 'mpremote' not found. Install it with: pip install mpremote" >&2
  exit 1
fi

if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

FLOW="$(echo "$1" | tr '[:upper:]' '[:lower:]')"
shift

PORT=""
CLEAN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --port)
      PORT="${2:-}"
      if [[ -z "$PORT" ]]; then
        echo "Error: --port requires a value" >&2
        exit 1
      fi
      shift 2
      ;;
    --clean)
      CLEAN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Error: unknown argument '$1'" >&2
      usage
      exit 1
      ;;
  esac
done

MPR=(mpremote)
if [[ -n "$PORT" ]]; then
  MPR+=(connect "$PORT")
fi

run_mp() {
  "${MPR[@]}" "$@"
}

safe_rm() {
  local remote_path="$1"
  run_mp fs rm "$remote_path" >/dev/null 2>&1 || true
}

safe_mkdir() {
  local remote_path="$1"
  run_mp fs mkdir "$remote_path" >/dev/null 2>&1 || true
}

upload_v1() {
  if [[ "$CLEAN" -eq 1 ]]; then
    echo "Cleaning target files for V1..."
    safe_rm :main.py
    safe_rm :MOSbius.py
    safe_rm :connections.json
    safe_rm :config.json
    safe_rm :lib/bitstream_builder.py
    safe_rm :lib/config_validation.py
    safe_rm :lib/driver.py
    safe_rm :lib/register_map_equations.py
    safe_rm :lib/pin_name_to_sw_matrix_pin_number.json
    safe_rm :lib
  fi

  echo "Uploading V1 runtime to Pico root..."
  run_mp fs cp "$ROOT_DIR/V1/main.py" :main.py
  run_mp fs cp "$ROOT_DIR/V1/MOSbius.py" :MOSbius.py
  run_mp fs cp "$ROOT_DIR/V1/connections.json" :connections.json
}

upload_v2() {
  if [[ "$CLEAN" -eq 1 ]]; then
    echo "Cleaning target files for V2..."
    safe_rm :main.py
    safe_rm :config.json
    safe_rm :MOSbius.py
    safe_rm :connections.json
    safe_rm :lib/bitstream_builder.py
    safe_rm :lib/config_validation.py
    safe_rm :lib/driver.py
    safe_rm :lib/register_map_equations.py
    safe_rm :lib/pin_name_to_sw_matrix_pin_number.json
    safe_rm :lib
  fi

  echo "Uploading V2 runtime to Pico root..."
  safe_mkdir :lib
  run_mp fs cp "$ROOT_DIR/V2/main.py" :main.py
  run_mp fs cp "$ROOT_DIR/V2/config.json" :config.json
  run_mp fs cp "$ROOT_DIR/V2/lib/bitstream_builder.py" :lib/bitstream_builder.py
  run_mp fs cp "$ROOT_DIR/V2/lib/config_validation.py" :lib/config_validation.py
  run_mp fs cp "$ROOT_DIR/V2/lib/driver.py" :lib/driver.py
  run_mp fs cp "$ROOT_DIR/V2/lib/register_map_equations.py" :lib/register_map_equations.py
  run_mp fs cp "$ROOT_DIR/V2/lib/pin_name_to_sw_matrix_pin_number.json" :lib/pin_name_to_sw_matrix_pin_number.json
}

case "$FLOW" in
  v1) upload_v1 ;;
  v2) upload_v2 ;;
  *)
    echo "Error: flow must be 'v1' or 'v2'" >&2
    usage
    exit 1
    ;;
esac

echo "Done."
