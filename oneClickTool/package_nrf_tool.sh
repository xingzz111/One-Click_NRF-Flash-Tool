#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_NAME="MagicTool"
DIST_DIR="$ROOT_DIR/dist_universal2"
BUILD_DIR="$ROOT_DIR/build_universal2"
SPEC_DIR="$ROOT_DIR/spec_universal2"

# Prefer project venv python, fallback to system python3.
PYTHON_BIN="${PYTHON_BIN:-$ROOT_DIR/.venv_pyi311/bin/python3}"
if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="$(command -v python3)"
fi

if [[ -z "${PYTHON_BIN:-}" ]]; then
  echo "[ERROR] python3 not found."
  exit 1
fi

echo "[INFO] Python: $PYTHON_BIN"

# Optional override: SSHPASS_BIN=/absolute/path/to/sshpass ./package_nrf_tool.sh
SSHPASS_SOURCE=""
if [[ -n "${SSHPASS_BIN:-}" && -x "${SSHPASS_BIN:-}" ]]; then
  SSHPASS_SOURCE="$SSHPASS_BIN"
elif [[ -x "$ROOT_DIR/bin/sshpass" ]]; then
  SSHPASS_SOURCE="$ROOT_DIR/bin/sshpass"
elif [[ -x "$ROOT_DIR/third_party/sshpass/sshpass" ]]; then
  SSHPASS_SOURCE="$ROOT_DIR/third_party/sshpass/sshpass"
fi

ADD_DATA_ARGS=("--add-data" "$ROOT_DIR/mix:mix")
if [[ -n "$SSHPASS_SOURCE" ]]; then
  echo "[INFO] Bundle sshpass: $SSHPASS_SOURCE"
  ADD_DATA_ARGS+=("--add-data" "$SSHPASS_SOURCE:bin/sshpass")
else
  echo "[WARN] sshpass binary not found. Package will use SSH_ASKPASS fallback at runtime."
  echo "       Put executable at '$ROOT_DIR/bin/sshpass' to bundle it."
fi

mkdir -p "$DIST_DIR" "$BUILD_DIR" "$SPEC_DIR"
rm -rf "$DIST_DIR/$APP_NAME"

echo "[INFO] Building $APP_NAME (target-arch: universal2)..."
"$PYTHON_BIN" -m PyInstaller \
  --noconfirm \
  --clean \
  --name "$APP_NAME" \
  --console \
  --onefile \
  --target-arch universal2 \
  --distpath "$DIST_DIR" \
  --workpath "$BUILD_DIR" \
  --specpath "$SPEC_DIR" \
  "${ADD_DATA_ARGS[@]}" \
  "$ROOT_DIR/nrf_oneclick_program.py"

echo "[INFO] Done."
echo "       Output: $DIST_DIR/$APP_NAME"
