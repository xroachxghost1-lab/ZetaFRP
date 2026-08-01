#!/usr/bin/env python3
"""
Zeta FRP Wizard — USB Driver Installer
========================================
Automated installation of USB drivers required for
Android device communication.

Supported drivers:
- Google USB Driver (ADB/Fastboot)
- Samsung USB Driver
- Qualcomm HS-USB QDLoader (EDL)
- MediaTek VCOM USB Driver

ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
Unauthorised use, distribution, or reproduction is an act of war.
Copyright © 2026 Zeta Omniverse. All rights reserved.
"""

import subprocess
import sys
import os
from pathlib import Path
from typing import List, Tuple

from zeta_frp.utils.logger import get_logger

logger = get_logger(__name__)

class DriverInstaller:
    """
    Cross-platform driver installation manager.

    On Windows, uses PnPUtil and driver packages.
    On Linux, configures udev rules.
    On macOS, no special drivers needed (uses built-in).
    """

    def __init__(self):
        self._platform = sys.platform
        self._resources_dir = (
            Path(__file__).parent.parent.parent / "resources" / "drivers"
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_required_drivers(self) -> List[str]:
        """
        Get list of required drivers for the current platform.

        Returns:
            List of driver names that should be installed.
        """
        if self._platform.startswith("win"):
            return [
                "Google USB Driver (ADB/Fastboot)",
                "Samsung USB Driver",
                "Qualcomm HS-USB QDLoader 9008",
                "MediaTek VCOM USB Driver",
            ]
        elif self._platform.startswith("linux"):
            return [
                "Android udev rules",
            ]
        else:
            return []  # macOS uses built-in drivers

    def check_drivers(self) -> List[Tuple[str, bool]]:
        """
        Check which drivers are currently installed.

        Returns:
            List of (driver_name, is_installed) tuples.
        """
        results = []
        for driver in self.get_required_drivers():
            installed = self._is_driver_installed(driver)
            results.append((driver, installed))
        return results

    def install_all(self) -> bool:
        """
        Attempt to install all required drivers.

        Returns:
            True if all installations succeeded (or were skipped on unsupported platforms).
        """
        if self._platform.startswith("darwin"):
            logger.info("macOS uses built-in drivers. No installation needed.")
            return True

        all_ok = True
        for driver, installed in self.check_drivers():
            if not installed:
                logger.info(f"Installing: {driver}")
                ok = self._install_driver(driver)
                if not ok:
                    logger.warning(f"Driver installation skipped: {driver}")
                    all_ok = False
        return all_ok

    def install_adb_drivers(self) -> bool:
        """Install only ADB/Fastboot drivers."""
        if self._platform.startswith("win"):
            return self._install_windows_driver("google_adb")
        elif self._platform.startswith("linux"):
            return self._install_linux_udev_rules()
        return True

    def install_samsung_drivers(self) -> bool:
        """Install Samsung USB drivers."""
        if self._platform.startswith("win"):
            return self._install_windows_driver("samsung")
        return True  # Linux/macOS use built-in

    def install_qualcomm_drivers(self) -> bool:
        """Install Qualcomm EDL drivers."""
        if self._platform.startswith("win"):
            return self._install_windows_driver("qualcomm")
        return True

    def install_mediatek_drivers(self) -> bool:
        """Install MediaTek VCOM drivers."""
        if self._platform.startswith("win"):
            return self._install_windows_driver("mediatek")
        return True

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _is_driver_installed(self, driver_name: str) -> bool:
        """Check if a specific driver is installed."""
        if self._platform.startswith("win"):
            return self._check_windows_driver(driver_name)
        elif self._platform.startswith("linux"):
            return self._check_linux_udev()
        return True

    def _install_driver(self, driver_name: str) -> bool:
        """Install a specific driver."""
        if "ADB" in driver_name or "Google" in driver_name:
            return self.install_adb_drivers()
        elif "Samsung" in driver_name:
            return self.install_samsung_drivers()
        elif "Qualcomm" in driver_name:
            return self.install_qualcomm_drivers()
        elif "MediaTek" in driver_name:
            return self.install_mediatek_drivers()
        return False

    def _check_windows_driver(self, driver_name: str) -> bool:
        """Check Windows driver installation via PnPUtil."""
        try:
            result = subprocess.run(
                ["pnputil", "/enum-drivers"],
                capture_output=True, text=True, timeout=30,
            )
            # Simple string matching for known driver names
            checks = {
                "google": "Google" in result.stdout,
                "samsung": "Samsung" in result.stdout,
                "qualcomm": "Qualcomm" in result.stdout,
                "mediatek": "MediaTek" in result.stdout,
            }
            for key in checks:
                if key in driver_name.lower():
                    return checks[key]
            return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _install_windows_driver(self, driver_type: str) -> bool:
        """
        Install a Windows driver from bundled driver package.

        Uses PnPUtil to install the driver .inf file.
        """
        driver_dirs = {
            "google_adb": self._resources_dir / "google" / "usb_driver",
            "samsung": self._resources_dir / "samsung",
            "qualcomm": self._resources_dir / "qualcomm",
            "mediatek": self._resources_dir / "mediatek",
        }

        driver_dir = driver_dirs.get(driver_type)
        if not driver_dir or not driver_dir.exists():
            logger.warning(
                f"Driver package not found for {driver_type} at {driver_dir}. "
                f"Please download drivers manually:\n"
                f"  Google USB: https://developer.android.com/studio/run/win-usb\n"
                f"  Samsung: https://developer.samsung.com/android-usb-driver\n"
                f"  Qualcomm: Search for 'Qualcomm HS-USB QDLoader 9008 driver'\n"
                f"  MediaTek: Search for 'MediaTek VCOM USB driver'"
            )
            return False

        # Find .inf files
        inf_files = list(driver_dir.glob("*.inf"))
        if not inf_files:
            logger.warning(f"No .inf files found in {driver_dir}")
            return False

        for inf in inf_files:
            try:
                result = subprocess.run(
                    ["pnputil", "/add-driver", str(inf), "/install"],
                    capture_output=True, text=True, timeout=60,
                )
                if result.returncode == 0:
                    logger.info(f"Driver installed: {inf.name}")
                    return True
                else:
                    logger.warning(f"Driver install failed: {inf.name} — {result.stderr}")
            except subprocess.TimeoutExpired:
                logger.error(f"Driver install timed out: {inf.name}")

        return False

    def _check_linux_udev(self) -> bool:
        """Check if Android udev rules are installed."""
        udev_path = Path("/etc/udev/rules.d/51-android.rules")
        return udev_path.exists()

    def _install_linux_udev_rules(self) -> bool:
        """Install Android udev rules on Linux."""
        udev_content = (
            '# Android ADB/Fastboot udev rules\n'
            'SUBSYSTEM=="usb", ATTR{idVendor}=="18d1", MODE="0666", GROUP="plugdev"\n'
            'SUBSYSTEM=="usb", ATTR{idVendor}=="05c6", MODE="0666", GROUP="plugdev"\n'
            'SUBSYSTEM=="usb", ATTR{idVendor}=="0e8d", MODE="0666", GROUP="plugdev"\n'
            'SUBSYSTEM=="usb", ATTR{idVendor}=="04e8", MODE="0666", GROUP="plugdev"\n'
            'SUBSYSTEM=="usb", ATTR{idVendor}=="2ae5", MODE="0666", GROUP="plugdev"\n'
        )

        udev_path = Path("/etc/udev/rules.d/51-android.rules")

        try:
            # Try to write with sudo-like behavior
            if os.geteuid() == 0:
                with open(udev_path, "w") as f:
                    f.write(udev_content)
                subprocess.run(["udevadm", "control", "--reload-rules"], timeout=10)
                subprocess.run(["udevadm", "trigger"], timeout=10)
                logger.info("Android udev rules installed")
                return True
            else:
                logger.warning(
                    "Root access required to install udev rules. Run:\n"
                    f"  sudo echo '{udev_content}' > {udev_path}\n"
                    "  sudo udevadm control --reload-rules\n"
                    "  sudo udevadm trigger"
                )
                return False
        except Exception as e:
            logger.error(f"Failed to install udev rules: {e}")
            return False
