#!/usr/bin/env bash
# Zeta FRP Wizard — Interactive installer
# Places: zeta-frp-wizard/scripts/install.sh
# Features:
# - Interactive menu for install / uninstall / build
# - Auto-detects Python, pip, venv, and user bin path
# - Adds user bin to shell rc if needed
# - Calls existing platform build scripts when requested

set -euo pipefail

PROJECT_NAME="Zeta FRP Wizard"
PY_PACKAGE_NAME="zeta-frp-wizard"
CONSOLE_CMD="zeta-frp"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOGFILE="$REPO_ROOT/.install.log"
DRY_RUN=false

log() { printf '%s\n' "$(date -u +'%Y-%m-%dT%H:%M:%SZ') | %s" "$*" | tee -a "$LOGFILE"; }
err() { printf 'ERROR: %s\n' "$*" >&2; log "ERROR: $*"; exit 1; }
run_cmd() {
  if [ "$DRY_RUN" = true ]; then
    log "[DRY RUN] $*"
  else
    log "[RUN] $*"
    eval "$@"
  fi
}

confirm() {
  local prompt="$1"; shift
  local default=${1:-N}
  read -r -p "$prompt [$default] " ans
  case "$ans" in
    [Yy]|[Yy][Ee][Ss]) return 0 ;;
    *) return 1 ;;
  esac
}

detect_python() {
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD=python3
  elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD=python
  else
    err "Python not found. Please install Python 3.11+"
  fi
  # verify version
  PY_VER=$($PYTHON_CMD -c 'import sys; print("%d.%d" % sys.version_info[:2])') || true
  log "Using $PYTHON_CMD (version $PY_VER)"
}

get_user_bin() {
  # user base bin path
  USER_BASE=$($PYTHON_CMD -m site --user-base 2>/dev/null || echo "")
  if [ -n "$USER_BASE" ]; then
    if [ "$(uname -s)" = "Darwin" ] || [ "$(uname -s)" = "Linux" ]; then
      USER_BIN="$USER_BASE/bin"
    else
      USER_BIN="$USER_BASE/Scripts"
    fi
  else
    USER_BIN="$HOME/.local/bin"
  fi
  log "User bin: $USER_BIN"
}

path_in_shell_rc() {
  local candidate="$1"
  for rc in "$HOME/.profile" "$HOME/.bash_profile" "$HOME/.bashrc" "$HOME/.zshrc"; do
    if [ -f "$rc" ] && grep -qF "$candidate" "$rc"; then
      return 0
    fi
  done
  return 1
}

add_path_to_shell_rc() {
  local candidate="$1"
  local marker="# Added by ${PY_PACKAGE_NAME} installer"
  if path_in_shell_rc "$candidate"; then
    log "$candidate already present in shell rc"
    return 0
  fi
  if [ "$DRY_RUN" = true ]; then
    log "[DRY RUN] Would add PATH export for $candidate to ~/.profile"
    return 0
  fi
  if [ -f "$HOME/.profile" ]; then
    printf "\n%s\nexport PATH=\"%s:\$PATH\"\n" "$marker" "$candidate" >> "$HOME/.profile"
    log "Added PATH export to $HOME/.profile"
  else
    printf "\n%s\nexport PATH=\"%s:\$PATH\"\n" "$marker" "$candidate" >> "$HOME/.bashrc"
    log "Added PATH export to $HOME/.bashrc"
  fi
}

ensure_dir() { local dir="$1"; if [ "$DRY_RUN" = true ]; then log "[DRY RUN] mkdir -p $dir"; else mkdir -p "$dir"; fi }

pip_install_user() {
  log "Installing $PY_PACKAGE_NAME into user site-packages (pip --user)"
  run_cmd "$PYTHON_CMD -m pip install --upgrade pip setuptools wheel"
  run_cmd "$PYTHON_CMD -m pip install --user \"$REPO_ROOT\""
  log "Installed (user)"
}

pip_install_editable() {
  log "Installing $PY_PACKAGE_NAME in editable mode (dev)"
  run_cmd "$PYTHON_CMD -m pip install --upgrade pip setuptools wheel"
  run_cmd "$PYTHON_CMD -m pip install -e \"$REPO_ROOT\"[dev]"
  log "Installed (editable)"
}

pip_install_venv() {
  local venv_dir="$1"
  log "Creating venv at $venv_dir and installing package"
  run_cmd "$PYTHON_CMD -m venv \"$venv_dir\""
  # shellcheck disable=SC1090
  run_cmd "source \"$venv_dir/bin/activate\" && python -m pip install --upgrade pip setuptools wheel && python -m pip install \"$REPO_ROOT\""
  log "Installed into venv: $venv_dir"
}

pip_uninstall() {
  log "Uninstalling $PY_PACKAGE_NAME via pip (user/system as available)"
  if run_cmd "$PYTHON_CMD -m pip show $PY_PACKAGE_NAME >/dev/null 2>&1"; then
    run_cmd "$PYTHON_CMD -m pip uninstall -y $PY_PACKAGE_NAME"
    log "pip uninstall attempted"
  else
    log "Package not found in pip metadata. Will attempt to remove console entry if present."
  fi

  # remove console script from user bin if present
  get_user_bin
  if [ -x "$USER_BIN/$CONSOLE_CMD" ]; then
    run_cmd "rm -f \"$USER_BIN/$CONSOLE_CMD\""
    log "Removed $USER_BIN/$CONSOLE_CMD"
  fi
}

install_symlink_if_needed() {
  get_user_bin
  # pip --user installs console scripts to $USER_BIN. If not in PATH, offer to add.
  if [ -x "$USER_BIN/$CONSOLE_CMD" ]; then
    log "$CONSOLE_CMD is installed at $USER_BIN/$CONSOLE_CMD"
    if ! command -v "$CONSOLE_CMD" >/dev/null 2>&1; then
      log "$CONSOLE_CMD not in PATH"
      if confirm "Add $USER_BIN to your PATH in shell rc? (recommended)" Y; then
        add_path_to_shell_rc "$USER_BIN"
      fi
    fi
  else
    log "$CONSOLE_CMD not found in $USER_BIN"
  fi
}

build_macos_app() {
  if [ "$(uname -s)" != "Darwin" ]; then
    err "macOS build must be run on macOS host"
  fi
  if [ ! -x "$REPO_ROOT/zeta-frp-wizard/scripts/build_macos.sh" ]; then
    err "macOS build script not found or not executable: scripts/build_macos.sh"
  fi
  run_cmd "bash \"$REPO_ROOT/zeta-frp-wizard/scripts/build_macos.sh\""
}

build_windows_exe() {
  if [ "$(uname -s)" = "Darwin" ]; then
    log "Windows build script exists but must be run on Windows or CI that supports Windows builds."
  fi
  if [ ! -f "$REPO_ROOT/zeta-frp-wizard/scripts/build_windows.bat" ]; then
    err "Windows build script not found: scripts/build_windows.bat"
  fi
  log "To build on Windows run: scripts/build_windows.bat from a Windows shell (or set up wine/ci)"
}

show_menu() {
  cat <<EOF
$PROJECT_NAME — Interactive installer

1) Install (pip --user)          - install the package into your user site-packages
2) Install (editable, dev)       - pip install -e .[dev]
3) Install into venv             - create venv and install there
4) Build macOS .app (pyinstaller) - runs scripts/build_macos.sh (macOS only)
5) Build Windows .exe            - info / runs script on Windows
6) Uninstall                     - pip uninstall + remove console script
7) Add user bin to PATH          - add ~/.local/bin (or user base) to shell rc
8) Dry-run toggle (currently: $DRY_RUN)
9) Quit
EOF
}

main() {
  detect_python
  get_user_bin
  log "Log file: $LOGFILE"

  while true; do
    show_menu
    read -r -p "Choose an option [1-9]: " choice
    case "$choice" in
      1)
        pip_install_user
        install_symlink_if_needed
        ;;
      2)
        pip_install_editable
        install_symlink_if_needed
        ;;
      3)
        read -r -p "Venv path (default: $REPO_ROOT/.venv): " venvp
        venvp=${venvp:-$REPO_ROOT/.venv}
        pip_install_venv "$venvp"
        ;;
      4)
        if confirm "Run macOS build script now?" N; then
          build_macos_app
        fi
        ;;
      5)
        if confirm "Show Windows build instructions?" Y; then
          build_windows_exe
        fi
        ;;
      6)
        if confirm "Really uninstall $PY_PACKAGE_NAME?" N; then
          pip_uninstall
        fi
        ;;
      7)
        if confirm "Add $USER_BIN to PATH in your shell rc?" Y; then
          add_path_to_shell_rc "$USER_BIN"
        fi
        ;;
      8)
        DRY_RUN=$([ "$DRY_RUN" = true ] && echo false || echo true)
        log "DRY_RUN set to $DRY_RUN"
        ;;
      9|q|Q)
        log "Exiting"
        exit 0
        ;;
      *)
        echo "Invalid selection"
        ;;
    esac
    echo
  done
}

main "$@"
