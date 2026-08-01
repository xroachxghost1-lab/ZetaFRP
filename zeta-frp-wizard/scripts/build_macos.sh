#!/usr/bin/env bash
# ================================================================
# Zeta FRP Wizard — macOS Build Script (improved)
# Builds a standalone .app bundle using PyInstaller
# - safer dependency handling
# - optional dry-run, deps-only, clean
# - checks for resources and Python
# ================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_CMD=""
DRY_RUN=false
CLEAN=false
DEPS_ONLY=false
BUILD=true

log() { printf '%s\n' "$(date -u +'%Y-%m-%dT%H:%M:%SZ') | %s" "$*"; }
err() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
run_cmd() {
  if [ "$DRY_RUN" = true ]; then
    log "[DRY RUN] $*"
  else
    log "[RUN] $*"
    eval "$@"
  fi
}

usage() {
  cat <<EOF
Usage: $(basename "$0") [--dry-run] [--deps-only] [--clean] [--no-build]

Options:
  --dry-run    Show commands without executing
  --deps-only  Only install Python deps
  --clean      Remove previous build artifacts and exit
  --no-build   Do not run the PyInstaller build
EOF
  exit 1
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --dry-run) DRY_RUN=true; shift ;;
    --deps-only) DEPS_ONLY=true; shift ;;
    --clean) CLEAN=true; shift ;;
    --no-build) BUILD=false; shift ;;
    -h|--help) usage ;;
    *) echo "Unknown arg: $1"; usage ;;
  esac
done

# detect python3
if command -v python3 >/dev/null 2>&1; then
  PYTHON_CMD=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON_CMD=python
else
  err "Python 3 not found. Install Python 3.11+ and try again."
fi

log "Using $PYTHON_CMD"

cd "$REPO_ROOT"

APP_NAME="Zeta FRP Wizard"
MAIN_PY="zeta_frp/main.py"
ICON_PATH="resources/icons/zeta.icns"
EXTRA_DATA="resources:resources"
DIST_DIR="dist"
BUILD_DIR="build"

# Clean
if [ "$CLEAN" = true ]; then
  log "Cleaning previous build artifacts"
  run_cmd "rm -rf \"$DIST_DIR\" \"$BUILD_DIR\"" || true
  exit 0
fi

# Ensure main entry exists
if [ ! -f "$MAIN_PY" ]; then
  err "Main entry point not found: $MAIN_PY"
fi

# Ensure icon exists (optional)
if [ ! -f "$ICON_PATH" ]; then
  log "Warning: icon not found at $ICON_PATH — continuing without custom icon"
  ICON_ARG=""
else
  ICON_ARG="--icon $ICON_PATH"
fi

# Install dependencies
log "Installing Python dependencies (requirements.txt) using user site or venv"
if [ -f "requirements.txt" ]; then
  run_cmd "$PYTHON_CMD -m pip install --upgrade pip setuptools wheel"
  run_cmd "$PYTHON_CMD -m pip install -r requirements.txt"
else
  log "No requirements.txt found — skipping"
fi

# Ensure pyinstaller
if ! $PYTHON_CMD -m pip show pyinstaller >/dev/null 2>&1; then
  log "pyinstaller not found; installing pyinstaller"
  run_cmd "$PYTHON_CMD -m pip install pyinstaller"
fi

if [ "$DEPS_ONLY" = true ]; then
  log "Deps-only requested — exiting after installing dependencies"
  exit 0
fi

# Remove previous build output
log "Removing previous dist/build directories"
run_cmd "rm -rf \"$DIST_DIR\" \"$BUILD_DIR\"" || true

if [ "$BUILD" = true ]; then
  log "Building .app bundle with PyInstaller"
  # Use --add-data format cross-platform for pyinstaller; on macOS it's src:dest
  # Quote paths to allow spaces
  run_cmd "$PYTHON_CMD -m PyInstaller --name \"$APP_NAME\" --onefile --windowed --osx-bundle-identifier com.zeta.frpwizard $ICON_ARG --add-data \"$EXTRA_DATA\" --hidden-import PySide6.QtCore --hidden-import PySide6.QtWidgets --hidden-import PySide6.QtGui \"$MAIN_PY\""
  log "Build complete"
  log "Output: $DIST_DIR/$APP_NAME.app (or $DIST_DIR/$APP_NAME)"
fi

exit 0
