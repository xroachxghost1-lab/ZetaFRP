#!/usr/bin/env python3
"""
Zeta FRP Wizard — Samsung Odin Flasher Plugin
==============================================
Wraps Odin3 for flashing Samsung combination firmware
to bypass FRP on Samsung devices.

ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
Unauthorised use, distribution, or reproduction is an act of war.
Copyright © 2026 Zeta Omniverse. All rights reserved.
"""

import subprocess
import os
import time
from pathlib import Path
from typing import Optional, List, Dict

from zeta_frp.plugins.base import FRPBypassPlugin, PluginResult, PluginStatus
from zeta_frp.utils.logger import get_logger

logger = get_logger(__name__)

class SamsungOdinPlugin(FRPBypassPlugin):
    """
    Samsung FRP bypass via Odin combination firmware flashing.

    Process:
    1. Detect Samsung device in Download Mode or ADB
    2. Download/verify combination firmware
    3. Flash via Odin
    4. Execute ADB FRP bypass on factory binary
    5. Optionally flash stock firmware back
    """

    @property
    def plugin_name(self) -> str:
        return "Samsung Odin Combination Firmware Bypass"

    @property
    def plugin_version(self) -> str:
        return "1.0.0"

    @property
    def supported_brands(self) -> List[str]:
        return ["samsung"]

    @property
    def supported_socs(self) -> List[str]:
        return []  # All Samsung SoCs

    # ------------------------------------------------------------------
    # Compatibility
    # ------------------------------------------------------------------

    def check_compatibility(self, device_info: Dict) -> PluginResult:
        manufacturer = device_info.get("ro.product.manufacturer", "").lower()
        if "samsung" not in manufacturer:
            return PluginResult(
                success=False,
                message="This plugin only supports Samsung devices.",
                status=PluginStatus.FAILED,
            )
        return PluginResult(
            success=True,
            message="Samsung device detected. Odin method available.",
            data={"model": device_info.get("ro.product.model", "Unknown")},
        )

    # ------------------------------------------------------------------
    # Pre-Flight
    # ------------------------------------------------------------------

    def pre_flight_checks(self, device_info: Dict) -> List[str]:
        warnings = []
        model = device_info.get("ro.product.model", "")

        if not model:
            warnings.append("Cannot determine device model. Firmware compatibility cannot be verified.")

        # Check if Odin is available
        odin_path = self._find_odin()
        if not odin_path:
            warnings.append(
                "Odin3 not found. Download Odin3 from: "
                "https://odindownload.com/ and place it in the resources/odin/ directory."
            )

        return warnings

    # ------------------------------------------------------------------
    # Required Files
    # ------------------------------------------------------------------

    def get_required_files(self, device_info: Dict) -> List[str]:
        model = device_info.get("ro.product.model", "")
        return [
            f"Combination firmware for {model} (COMBINATION_*.tar.md5)",
            "Odin3 v3.14+ (included with Zeta FRP Wizard)",
            "Samsung USB Drivers (included with Zeta FRP Wizard)",
        ]

    # ------------------------------------------------------------------
    # Execute Bypass
    # ------------------------------------------------------------------

    def execute_bypass(self, device_info: Dict,
                       firmware_path: Optional[str] = None,
                       progress_callback=None) -> PluginResult:
        logger.info("Starting Samsung Odin FRP bypass...")

        if progress_callback:
            progress_callback(0, "Starting Samsung Odin bypass...")

        # Step 1: Verify Odin availability
        odin_path = self._find_odin()
        if not odin_path:
            return PluginResult(
                success=False,
                message="Odin3 not found. Please install Odin3 and try again.",
                status=PluginStatus.FAILED,
            )

        if progress_callback:
            progress_callback(10, "Odin3 detected")

        # Step 2: Boot into Download Mode
        device_serial = device_info.get("ro.serialno", "")
        if device_serial:
            self._boot_to_download(device_serial)

        if progress_callback:
            progress_callback(20, "Waiting for Download Mode...")
        time.sleep(5)

        # Step 3: Verify firmware
        if not firmware_path or not Path(firmware_path).exists():
            return PluginResult(
                success=False,
                message=(
                    "Combination firmware not provided. Use the Firmware Downloader "
                    "to obtain the correct combination firmware for your device model."
                ),
                status=PluginStatus.FAILED,
            )

        if progress_callback:
            progress_callback(30, f"Firmware loaded: {Path(firmware_path).name}")

        # Step 4: Flash firmware via Odin
        if progress_callback:
            progress_callback(40, "Flashing combination firmware via Odin...")

        flash_result = self._flash_with_odin(odin_path, firmware_path)

        if not flash_result.success:
            return flash_result

        if progress_callback:
            progress_callback(70, "Firmware flashed. Waiting for device reboot...")

        # Wait for device to boot
        time.sleep(30)

        # Step 5: ADB FRP bypass on factory binary
        if progress_callback:
            progress_callback(80, "Executing ADB FRP bypass...")

        bypass_result = self._execute_adb_bypass(device_serial)

        if progress_callback:
            progress_callback(95, "FRP bypass complete. Rebooting...")

        # Step 6: Reboot
        from zeta_frp.utils.adb_wrapper import ADBWrapper
        adb = ADBWrapper()
        adb.reboot(serial=device_serial)
        time.sleep(5)

        if progress_callback:
            progress_callback(100, "Samsung FRP bypass completed successfully!")

        return PluginResult(
            success=True,
            message="Samsung FRP bypass completed. Device rebooting.",
            data={"method": "odin_combination"},
            status=PluginStatus.SUCCESS,
        )

    # ------------------------------------------------------------------
    # Internal Methods
    # ------------------------------------------------------------------

    def _find_odin(self) -> Optional[str]:
        """Locate Odin3 executable."""
        base = Path(__file__).parent.parent.parent.parent / "resources" / "odin"

        if os.name == "nt":
            candidates = [
                base / "Odin3_v3.14.4" / "Odin3.exe",
                base / "odin3.exe",
                base / "Odin3.exe",
            ]
        else:
            # Odin is Windows-only; on Linux/Mac, look for Heimdall
            import shutil
            heimdall = shutil.which("heimdall")
            if heimdall:
                return heimdall
            return None

        for c in candidates:
            if c.exists():
                return str(c)
        return None

    def _boot_to_download(self, serial: str) -> None:
        """Boot Samsung device into Download/Odin mode."""
        from zeta_frp.utils.adb_wrapper import ADBWrapper
        adb = ADBWrapper()
        # Samsung-specific reboot to download mode
        result = adb.shell("reboot download", serial=serial)
        if not result.success:
            # Fallback: reboot bootloader then use key combo
            adb.reboot("bootloader", serial=serial)
        logger.info("Device rebooting to Download Mode...")

    def _flash_with_odin(self, odin_path: str, firmware_path: str) -> PluginResult:
        """
        Execute Odin flash command.

        Odin command-line usage:
        Odin3.exe -b <BL> -a <AP> -c <CP> -s <CSC> [-u <UMS>]
        """
        firmware_file = Path(firmware_path)

        cmd = [odin_path]

        # If firmware is a single tar.md5 (combination firmware)
        if firmware_file.suffix.lower() in (".tar", ".md5") or ".tar.md5" in firmware_file.name.lower():
            cmd.extend(["-a", str(firmware_file)])
        else:
            # Multi-file firmware
            for f in sorted(firmware_file.parent.glob("*")):
                fname = f.name.upper()
                if fname.startswith("BL_"):
                    cmd.extend(["-b", str(f)])
                elif fname.startswith("AP_"):
                    cmd.extend(["-a", str(f)])
                elif fname.startswith("CP_"):
                    cmd.extend(["-c", str(f)])
                elif fname.startswith("CSC_"):
                    cmd.extend(["-s", str(f)])
                elif fname.startswith("HOME_CSC"):
                    cmd.extend(["-s", str(f)])

        logger.info(f"Odin command: {' '.join(cmd)}")

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout for flashing
                cwd=Path(odin_path).parent,
            )
            stdout = proc.stdout
            stderr = proc.stderr

            if proc.returncode == 0 or "PASS" in stdout.upper():
                logger.info("Odin flash successful")
                return PluginResult(
                    success=True,
                    message="Firmware flashed successfully via Odin.",
                    data={"odin_output": stdout},
                )
            else:
                logger.error(f"Odin flash failed: {stdout}\n{stderr}")
                return PluginResult(
                    success=False,
                    message=f"Odin flash failed: {stderr or stdout}",
                    status=PluginStatus.FAILED,
                )

        except subprocess.TimeoutExpired:
            return PluginResult(
                success=False,
                message="Odin flash timed out (5 minutes). Check USB connection.",
                status=PluginStatus.FAILED,
            )

    def _execute_adb_bypass(self, serial: str) -> PluginResult:
        """Execute Samsung-specific ADB FRP bypass commands."""
        from zeta_frp.utils.adb_wrapper import ADBWrapper
        from zeta_frp.plugins.samsung.adb_samsung import SamsungADBBypass

        adb = ADBWrapper()
        samsung_bypass = SamsungADBBypass(adb)
        return samsung_bypass.execute(serial)
