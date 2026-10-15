#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
BLENDER_BIN="${BLENDER_BIN:-/home/amrhares/tools/blender-5.2.2/blender}"
if [[ ! -x "$BLENDER_BIN" ]]; then BLENDER_BIN="$(command -v blender)"; fi
mkdir -p "$PROJECT_DIR/.runtime/config" "$PROJECT_DIR/.runtime/cache"
export BLENDER_USER_CONFIG="$PROJECT_DIR/.runtime/config"
export XDG_CACHE_HOME="$PROJECT_DIR/.runtime/cache"
exec "$BLENDER_BIN" -noaudio -b --factory-startup --python-exit-code 1 "$@"
