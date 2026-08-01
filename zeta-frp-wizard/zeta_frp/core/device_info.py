#!/usr/bin/env python3
"""
Zeta FRP Wizard — Device Information Reader
============================================
Enriches a DetectedDevice with detailed system properties
and provides helper methods for compatibility checks.

ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
Unauthorised use, distribution, or reproduction is an act of war.
Copyright © 2026 Zeta Omniverse. All rights reserved.
"""

from datetime import datetime
from typing import Optional

from zeta_frp.utils.logger import get_logger
from zeta_frp.utils.adb_wrapper import ADBWrapper

logger = get_logger(__name__)

class DeviceInfoReader:
    """
    Reads detailed device information via ADB.

    Usage:
        reader = DeviceInfoReader(adb_wrapper)
        info = reader.read_full(serial="abc123")
        print(info["ro.build.version.release"])
    """

    CRITICAL_PROPS = [
        "ro.product.manufacturer",
        "ro.product.model",
        "ro.product.name",
        "ro.product.device",
        "ro.build.version.release",
        "ro.build.version.sdk",
        "ro.build.version.security_patch",
        "ro.vendor.build.security_patch",
        "ro.board.platform",
        "ro.build.fingerprint",
        "ro.build.description",
        "ro.serialno",
    ]

    def __init__(self, adb: Optional[ADBWrapper] = None):
        self._adb = adb or ADBWrapper()

    def read_full(self, serial: Optional[str] = None) -> dict:
        """
        Read all available device properties.

        Returns:
            Dictionary of property_name -> value.
        """
        return self._adb.get_all_props(serial=serial)

    def read_critical(self, serial: Optional[str] = None) -> dict:
        """Read only critical properties needed for FRP operations."""
        props = self._adb.get_all_props(serial=serial)
        return {k: props.get(k, "") for k in self.CRITICAL_PROPS}

    def get_security_patch_date(self, serial: Optional[str] = None) -> Optional[datetime]:
        """
        Parse the security patch date from device properties.
        Returns None if unavailable.
        """
        props = self._adb.get_all_props(serial=serial)
        patch_str = props.get(
            "ro.vendor.build.security_patch",
            props.get("ro.build.version.security_patch", ""),
        )
        if not patch_str:
            return None
        try:
            return datetime.strptime(patch_str, "%Y-%m-%d")
        except ValueError:
            logger.warning(f"Could not parse security patch date: {patch_str}")
            return None

    def get_android_version(self, serial: Optional[str] = None) -> int:
        """Get the Android SDK level."""
        sdk = self._adb.get_prop("ro.build.version.sdk", serial)
        try:
            return int(sdk)
        except (ValueError, TypeError):
            return 0

    def is_usb_debugging_enabled(self, serial: Optional[str] = None) -> bool:
        """Check if USB debugging is enabled (only works if ADB is connected)."""
        result = self._adb.shell("settings get global adb_enabled", serial=serial)
        return result.success and result.stdout.strip() == "1"

    def get_imei(self, serial: Optional[str] = None) -> str:
        """Get the device IMEI for firmware download validation."""
        return self._adb.get_imei(serial=serial)

    def check_frp_locked(self, serial: Optional[str] = None) -> bool:
        """
        Attempt to determine if FRP is active on the device.
        This is an indirect check: if device is in setup wizard
        and certain properties are set, FRP is likely active.
        """
        props = self._adb.get_all_props(serial=serial)
        provisioned = props.get("ro.setupwizard.mode", "")
        setup_complete = props.get("user_setup_complete", "0")
        if provisioned == "OPTIONAL" or setup_complete == "0":
            return True
        return False
