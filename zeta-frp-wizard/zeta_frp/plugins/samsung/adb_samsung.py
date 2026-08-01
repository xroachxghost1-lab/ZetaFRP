#!/usr/bin/env python3
"""
Zeta FRP Wizard — Samsung ADB Bypass
=====================================
Samsung-specific ADB commands for FRP removal.
Samsung devices use Knox and additional security layers
that require specific ADB command sequences.

ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
Unauthorised use, distribution, or reproduction is an act of war.
Copyright © 2026 Zeta Omniverse. All rights reserved.
"""

from typing import Optional

from zeta_frp.plugins.base import PluginResult, PluginStatus
from zeta_frp.utils.logger import get_logger
from zeta_frp.utils.adb_wrapper import ADBWrapper, ADBResult

logger = get_logger(__name__)

class SamsungADBBypass:
    """
    Samsung-specific ADB FRP bypass commands.

    Samsung's FRP implementation differs from AOSP:
    - Additional Knox security layer
    - Samsung-specific settings keys
    - Samsung Account requirements
    """

    def __init__(self, adb: Optional[ADBWrapper] = None):
        self._adb = adb or ADBWrapper()

    def execute(self, serial: Optional[str] = None) -> PluginResult:
        """
        Execute the full Samsung ADB FRP bypass sequence.

        Returns:
            PluginResult with success status.
        """
        logger.info("Starting Samsung ADB FRP bypass sequence...")

        steps = [
            ("Disabling setup wizard", self._disable_setup_wizard),
            ("Setting user_setup_complete", self._set_user_setup_complete),
            ("Clearing Samsung account data", self._clear_samsung_account),
            ("Removing Google accounts", self._remove_google_accounts),
            ("Disabling FRP notifications", self._disable_frp_notifications),
            ("Launching Settings", self._launch_settings),
        ]

        results = []
        for step_name, step_func in steps:
            logger.debug(f"Samsung ADB step: {step_name}")
            result = step_func(serial)
            results.append(result)
            if not result.success:
                logger.warning(f"Step '{step_name}' failed: {result.stderr}")

        all_ok = all(r.success for r in results[:5])  # First 5 are critical
        return PluginResult(
            success=all_ok,
            message="Samsung ADB bypass completed" if all_ok else "Some steps failed",
            data={"steps": [r.stdout for r in results]},
            status=PluginStatus.SUCCESS if all_ok else PluginStatus.FAILED,
        )

    # ------------------------------------------------------------------
    # Individual Bypass Steps
    # ------------------------------------------------------------------

    def _disable_setup_wizard(self, serial: Optional[str] = None) -> ADBResult:
        """Disable the Samsung setup wizard."""
        commands = [
            "settings put secure user_setup_complete 1",
            "settings put global device_provisioned 1",
            "settings put global setup_wizard_has_run 1",
        ]
        results = []
        for cmd in commands:
            r = self._adb.shell(cmd, serial=serial)
            results.append(r)
        return self._combine_results(results, "Disable setup wizard")

    def _set_user_setup_complete(self, serial: Optional[str] = None) -> ADBResult:
        """Set user_setup_complete via content provider (more reliable)."""
        cmd = (
            "content insert --uri content://settings/secure "
            "--bind name:s:user_setup_complete --bind value:i:1"
        )
        return self._adb.shell(cmd, serial=serial)

    def _clear_samsung_account(self, serial: Optional[str] = None) -> ADBResult:
        """Clear Samsung account data."""
        commands = [
            "pm clear com.osp.app.signin",
            "pm clear com.samsung.android.scloud",
            "pm disable-user --user 0 com.samsung.android.scloud",
        ]
        results = []
        for cmd in commands:
            r = self._adb.shell(cmd, serial=serial)
            results.append(r)
        return self._combine_results(results, "Clear Samsung account")

    def _remove_google_accounts(self, serial: Optional[str] = None) -> ADBResult:
        """Remove Google accounts from device."""
        cmd = (
            "content delete --uri content://com.android.contacts/data/ "
            '--where "account_type=\'com.google\'"'
        )
        return self._adb.shell(cmd, serial=serial)

    def _disable_frp_notifications(self, serial: Optional[str] = None) -> ADBResult:
        """Disable FRP-related notifications and services."""
        commands = [
            "settings put secure frp_mode 0",
            "pm disable com.google.android.gms/.auth.frp.FrpNotification",
        ]
        results = []
        for cmd in commands:
            r = self._adb.shell(cmd, serial=serial)
            results.append(r)
        return self._combine_results(results, "Disable FRP notifications")

    def _launch_settings(self, serial: Optional[str] = None) -> ADBResult:
        """Launch Samsung Settings app."""
        return self._adb.shell(
            "am start -n com.android.settings/.Settings",
            serial=serial,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _combine_results(results: list, context: str) -> ADBResult:
        """Combine multiple ADB results into one."""
        all_ok = all(r.success for r in results)
        return ADBResult(
            success=all_ok,
            stdout="\n".join(r.stdout for r in results if r.stdout),
            stderr="\n".join(r.stderr for r in results if r.stderr),
            command=context,
        )
