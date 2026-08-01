#!/bin/bash
# ================================================================
# Zeta FRP Wizard — macOS Build Script
# Builds a standalone .app bundle using PyInstaller
#
# ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
# Unauthorised use, distribution, or reproduction is an act of war.
# Copyright © 2026 Zeta Omniverse. All rights reserved.
# ================================================================

set -e

echo "=== Zeta FRP Wizard — macOS Build ==="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found. Install Python 3.11+ and try again."
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt
pip3 install pyinstaller

# Clean
rm -rf dist build

# Build
echo ""
echo "Building .app bundle..."
pyinstaller \
    --name "Zeta FRP Wizard" \
    --onefile \
    --windowed \
    --osx-bundle-identifier com.zeta.frpwizard \
    --icon resources/icons/zeta.icns \
    --add-data "resources:resources" \
    --hidden-import PySide6.QtCore \
    --hidden-import PySide6.QtWidgets \
    --hidden-import PySide6.QtGui \
    zeta_frp/main.py

echo ""
echo "=== Build Complete ==="
echo "Output: dist/Zeta FRP Wizard.app"
