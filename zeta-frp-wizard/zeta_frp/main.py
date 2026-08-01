#!/usr/bin/env python3
"""
Zeta FRP Wizard — Application Entry Point
==========================================
Launches the PySide6 wizard GUI after performing pre-flight checks
for ADB, drivers, and platform compatibility.

ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
Unauthorised use, distribution, or reproduction is an act of war.
Copyright © 2026 Zeta Omniverse. All rights reserved.
"""

import sys
import os
import argparse
from pathlib import Path

from zeta_frp.utils.logger import get_logger, setup_logging
from zeta_frp.utils.config import ConfigManager

logger = get_logger(__name__)

def check_platform() -> str:
    """Determine the current platform and verify compatibility."""
    if sys.platform.startswith("win"):
        return "windows"
    elif sys.platform.startswith("darwin"):
        return "macos"
    elif sys.platform.startswith("linux"):
        return "linux"
    else:
        logger.error(f"Unsupported platform: {sys.platform}")
        sys.exit(1)

def check_adb_available() -> bool:
    """Check if ADB is available on the system PATH or bundled."""
    import shutil

    # Check bundled ADB first
    bundled_adb = Path(__file__).parent.parent / "resources" / "adb"
    if sys.platform.startswith("win"):
        bundled_adb = bundled_adb / "adb.exe"
    else:
        bundled_adb = bundled_adb / "adb"

    if bundled_adb.exists():
        os.environ["ADB_PATH"] = str(bundled_adb)
        return True

    # Check system PATH
    adb_path = shutil.which("adb")
    if adb_path:
        os.environ["ADB_PATH"] = adb_path
        return True

    return False

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Zeta FRP Wizard — Universal Factory Reset Protection Removal Tool",
        epilog="Zeta Omniverse — Alpha's Empire",
    )
    parser.add_argument(
        "--version", action="version", version=f"Zeta FRP Wizard v1.0.0"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging with verbose output",
    )
    parser.add_argument(
        "--no-gui",
        action="store_true",
        help="Run in CLI mode (headless operation for scripting)",
    )
    parser.add_argument(
        "--device",
        type=str,
        help="Target device serial number (for multi-device setups)",
    )
    parser.add_argument(
        "--method",
        type=str,
        choices=["adb", "odin", "edl", "spflash", "interactive", "auto"],
        default="auto",
        help="Force a specific bypass method (default: auto-detect)",
    )
    parser.add_argument(
        "--firmware",
        type=str,
        help="Path to firmware file for flashing-based methods",
    )
    return parser.parse_args()

def run_gui(args):
    """Launch the PySide6 wizard GUI."""
    try:
        from PySide6.QtWidgets import QApplication
        from zeta_frp.gui.main_window import MainWindow
    except ImportError as e:
        logger.critical(
            "PySide6 is required for GUI mode. Install with: pip install pyside6"
        )
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setApplicationName("Zeta FRP Wizard")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Zeta Omniverse")

    # Apply stylesheet
    from zeta_frp.gui.styles.theme import get_stylesheet

    app.setStyleSheet(get_stylesheet())

    window = MainWindow(debug=args.debug)
    window.show()

    logger.info("Zeta FRP Wizard GUI launched")
    sys.exit(app.exec())

def run_cli(args):
    """Run in headless CLI mode."""
    from zeta_frp.core.device_detector import DeviceDetector
    from zeta_frp.core.method_engine import MethodEngine

    logger.info("Running in CLI mode")
    detector = DeviceDetector()
    devices = detector.scan()

    if not devices:
        logger.error("No devices detected. Connect a device via USB and try again.")
        sys.exit(1)

    device = devices[0]
    logger.info(f"Detected: {device}")

    engine = MethodEngine()
    method = engine.select_method(device, force_method=args.method)
    logger.info(f"Selected method: {method.name}")

    result = method.execute(device, firmware_path=args.firmware)
    if result.success:
        logger.info("FRP bypass completed successfully!")
    else:
        logger.error(f"FRP bypass failed: {result.error}")

def main():
    """Main entry point."""
    args = parse_arguments()

    # Setup logging
    log_level = "DEBUG" if args.debug else "INFO"
    setup_logging(level=log_level)

    # Load configuration
    config = ConfigManager()
    config.load()

    # Platform check
    platform = check_platform()
    logger.info(f"Running on {platform}")

    # ADB availability warning (non-fatal, can be installed during wizard)
    if not check_adb_available():
        logger.warning(
            "ADB not found on PATH. The wizard will offer to install it."
        )

    if args.no_gui:
        run_cli(args)
    else:
        run_gui(args)

if __name__ == "__main__":
    main()
