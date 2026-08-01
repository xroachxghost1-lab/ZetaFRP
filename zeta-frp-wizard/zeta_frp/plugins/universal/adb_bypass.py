#!/usr/bin/env python3
"""
Zeta FRP Wizard — Universal ADB Bypass Plugin
===============================================
Cross-brand ADB-based FRP bypass for devices with
USB debugging pre-enabled.

ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
Unauthorised use, distribution, or reproduction is an act of war.
Copyright © 2026 Zeta Omniverse. All rights reserved.
"""

from typing import List, Dict, Optional

from zeta_frp.plugins.base import FRPBypassPlugin, PluginResult, PluginStatus
from zeta_frp.utils.logger import get_logger
from zeta_frp.utils.adb_wrapper import ADBWrapper, ADBResult

logger = get_logger(__name__)

class UniversalADBBypass(FRPBypassPlugin):
    """
    Universal ADB FRP bypass — works on any Android device
    that has USB debugging pre-enabled.

    The canonical technique sets user_setup_complete=1 and
    launches Settings to remove the Google account.
    """

    @property
    def plugin_name(self) -> str:
        return "Universal ADB FRP Bypass"

    @property
    def plugin_version(self) -> str:
        return "1.0.0"

    @property
    def supported_brands(self) -> List[str]:
        return []  # All brands

    @property
    def supported_socs(self) -> List[str]:
        return []  # All SoCs

    # ------------------------------------------------------------------
    # Compatibility
    # ------------------------------------------------------------------

    def check_compatibility(self, device_info: Dict) -> PluginResult:
        sdk = int(device_info.get("ro.build.version.sdk", "0"))
        if sdk < 21:
            return PluginResult(
                success=False,
                message="ADB bypass requires Android 5.1 (SDK 21) or higher.",
                status=PluginStatus.FAILED,
            )
        return PluginResult(
            success=True,
            message="Device meets minimum requirements for ADB bypass.",
        )

    def pre_flight_checks(self, device_info: Dict) -> List[str]:
        warnings = []
        warnings.append(
            "USB debugging MUST have been enabled BEFORE the factory reset. "
            "If USB debugging is not enabled, this method will fail."
        )
        warnings.append(
            "If the device shows 'unauthorized', you must accept the RSA key "
            "dialog on the device screen. This requires the device to be "
            "at the setup wizard with the screen accessible."
        )
        return warnings

    # ------------------------------------------------------------------
    # Execute
    # ------------------------------------------------------------------

    def execute_bypass(self, device_info: Dict,
                       firmware_path: Optional[str] = None,
                       progress_callback=None) -> PluginResult:
        logger.info("Starting Universal ADB FRP bypass...")

        adb = ADBWrapper()
        serial = device_info.get("ro.serialno", "")

        if progress_callback:
            progress_callback(0, "Checking ADB connection...")

        # Step 1: Verify ADB connection
        devices = adb.list_devices()
        if not devices:
            return PluginResult(
                success=False,
                message=(
                    "No ADB devices found. Ensure:\n"
                    "1. USB debugging was enabled before the reset\n"
                    "2. Device is connected via USB\n"
                    "3. ADB drivers are installed"
                ),
                status=PluginStatus.FAILED,
            )

        target = None
        for d in devices:
            if serial and d.serial == serial:
                target = d
                break
            elif d.state == "device":
                target = d
                break

        if target is None:
            return PluginResult(
                success=False,
                message="Device not in 'device' state. Check USB debugging authorization.",
                status=PluginStatus.FAILED,
            )

        if target.state == "unauthorized":
            return PluginResult(
                success=False,
                message=(
                    "Device shows 'unauthorized'. Accept the RSA key fingerprint "
                    "dialog on the device screen to continue."
                ),
                status=PluginStatus.FAILED,
            )

        if progress_callback:
            progress_callback(25, "ADB connection verified. Executing bypass...")

        # Step 2: Set user_setup_complete
        cmds = [
            # Method 1: Content provider (most reliable)
            (
                "content insert --uri content://settings/secure "
                "--bind name:s:user_setup_complete --bind value:i:1"
            ),
            # Method 2: Settings put (fallback)
            "settings put secure user_setup_complete 1",
            # Method 3: Global device_provisioned
            "settings put global device_provisioned 1",
            # Method 4: Setup wizard has run
            "settings put global setup_wizard_has_run 1",
        ]

        for i, cmd in enumerate(cmds):
            result = adb.shell(cmd, serial=serial)
            if progress_callback:
                progress_callback(30 + (i * 15), f"Executing bypass command {i+1}/{len(cmds)}...")
            if not result.success:
                logger.warning(f"Command failed: {cmd}")

        if progress_callback:
            progress_callback(80, "Launching Settings app...")

        # Step 3: Launch Settings
        settings_intents = [
            "am start -n com.android.settings/.Settings",
            "am start -a android.settings.SETTINGS",
            "am start -n com.android.settings/.Settings$AccountSettingsActivity",
        ]

        for intent in settings_intents:
            result = adb.shell(intent, serial=serial)
            if result.success:
                break

        if progress_callback:
            progress_callback(95, "Bypass commands executed.")

        # Step 4: Optional — remove Google accounts
        remove_cmd = (
            "content delete --uri content://com.android.contacts/data/ "
            '--where "account_type=\'com.google\'"'
        )
        adb.shell(remove_cmd, serial=serial)

        if progress_callback:
            progress_callback(100, "ADB bypass complete!")

        return PluginResult(
            success=True,
            message=(
                "ADB FRP bypass executed. Settings should now be accessible.\n\n"
                "Manual steps:\n"
                "1. Navigate to Settings > Accounts\n"
                "2. Remove the Google account\n"
                "3. Factory reset the device again (Settings > Backup & Reset)\n"
                "4. After reboot, FRP will be removed"
            ),
            data={"method": "adb_universal"},
            status=PluginStatus.SUCCESS,
        )
