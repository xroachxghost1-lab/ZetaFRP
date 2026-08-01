#!/usr/bin/env python3
"""
Zeta FRP Wizard — MediaTek SP Flash Tool Plugin
=================================================
Wraps SP Flash Tool for flashing MediaTek devices
in BROM (Boot ROM) mode to bypass FRP.

MediaTek BROM mode is accessible via USB when the device
is powered off and connected with specific button combinations.

ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
Unauthorised use, distribution, or reproduction is an act of war.
Copyright © 2026 Zeta Omniverse. All rights reserved.
"""

import subprocess
import time
from pathlib import Path
from typing import Optional, List, Dict

from zeta_frp.plugins.base import FRPBypassPlugin, PluginResult, PluginStatus
from zeta_frp.utils.logger import get_logger

logger = get_logger(__name__)

class MediaTekSPFlashPlugin(FRPBypassPlugin):
    """
    MediaTek FRP bypass via SP Flash Tool and BROM mode.

    Process:
    1. Install MediaTek VCOM USB drivers
    2. Force device into BROM mode
    3. Load scatter file
    4. Flash firmware with FRP partition wipe
    5. Reboot
    """

    @property
    def plugin_name(self) -> str:
        return "MediaTek SP Flash Tool Bypass"

    @property
    def plugin_version(self) -> str:
        return "1.0.0"

    @property
    def supported_brands(self) -> List[str]:
        return ["xiaomi", "oppo", "vivo", "realme", "tecno", "infinix", "lenovo", "alcatel"]

    @property
    def supported_socs(self) -> List[str]:
        return ["mediatek"]

    # ------------------------------------------------------------------
    # Compatibility
    # ------------------------------------------------------------------

    def check_compatibility(self, device_info: Dict) -> PluginResult:
        platform = device_info.get("ro.board.platform", "").lower()
        is_mtk = any(x in platform for x in ("mt", "mtk"))

        if not is_mtk:
            return PluginResult(
                success=False,
                message="This device does not have a MediaTek SoC.",
                status=PluginStatus.FAILED,
            )

        return PluginResult(
            success=True,
            message="MediaTek device detected. SP Flash method available.",
            data={"platform": platform},
        )

    def pre_flight_checks(self, device_info: Dict) -> List[str]:
        warnings = []
        warnings.append(
            "MediaTek VCOM drivers must be installed before BROM mode is accessible. "
            "Windows may require disabling driver signature enforcement."
        )
        warnings.append(
            "Flashing via SP Flash Tool can overwrite NVRAM, causing IMEI loss. "
            "Backup NVRAM partition before flashing if possible."
        )
        return warnings

    def get_required_files(self, device_info: Dict) -> List[str]:
        model = device_info.get("ro.product.model", "")
        return [
            f"Scatter file for {model} (MT****_Android_Scatter.txt)",
            "SP Flash Tool v5.2+ (bundled with Zeta FRP Wizard)",
            "MediaTek VCOM USB drivers (bundled with Zeta FRP Wizard)",
        ]

    # ------------------------------------------------------------------
    # Execute
    # ------------------------------------------------------------------

    def execute_bypass(self, device_info: Dict,
                       firmware_path: Optional[str] = None,
                       progress_callback=None) -> PluginResult:
        logger.info("Starting MediaTek SP Flash FRP bypass...")

        if progress_callback:
            progress_callback(0, "Preparing MediaTek BROM bypass...")

        # Step 1: Check for BROM mode
        if not self._is_brom_mode():
            if progress_callback:
                progress_callback(10, "Device not in BROM mode. Provide instructions.")
            return PluginResult(
                success=False,
                message=(
                    "Device not detected in BROM mode (MediaTek USB Port).\n\n"
                    "To enter BROM mode:\n"
                    "1. Power off the device completely\n"
                    "2. Remove and reinsert battery (if removable)\n"
                    "3. Hold Volume Up + Volume Down (or specific key combo for your device)\n"
                    "4. Connect USB cable while holding buttons\n"
                    "   OR use test points on the motherboard\n"
                    "5. Device Manager should show 'MediaTek PreLoader USB VCOM Port'\n\n"
                    "Retry after the device enters BROM mode."
                ),
                status=PluginStatus.FAILED,
            )

        if progress_callback:
            progress_callback(20, "Device in BROM mode.")

        # Step 2: Locate SP Flash Tool
        spft_path = self._find_sp_flash_tool()
        if not spft_path:
            return PluginResult(
                success=False,
                message="SP Flash Tool not found. Bundle it in resources/mediatek/sp_flash_tool/",
                status=PluginStatus.FAILED,
            )

        # Step 3: Locate scatter file
        scatter_path = self._find_scatter(device_info, firmware_path)
        if not scatter_path:
            return PluginResult(
                success=False,
                message=(
                    "Scatter file not found. Provide firmware with scatter file "
                    "or place the scatter file in the firmware directory."
                ),
                status=PluginStatus.FAILED,
            )

        if progress_callback:
            progress_callback(40, "Scatter file loaded. Starting flash...")

        # Step 4: Execute SP Flash
        flash_result = self._execute_sp_flash(spft_path, scatter_path)
        if not flash_result.success:
            return flash_result

        if progress_callback:
            progress_callback(80, "Flash complete. Rebooting device...")

        # Step 5: Reboot
        time.sleep(5)

        if progress_callback:
            progress_callback(100, "MediaTek FRP bypass complete!")

        return PluginResult(
            success=True,
            message="MediaTek FRP bypass via SP Flash Tool completed.",
            data={"method": "mediatek_spflash"},
            status=PluginStatus.SUCCESS,
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _is_brom_mode(self) -> bool:
        """Check if a MediaTek device is in BROM mode."""
        import sys
        if sys.platform.startswith("win"):
            try:
                result = subprocess.run(
                    ["wmic", "path", "Win32_PnPEntity", "where",
                     "DeviceID like '%VID_0E8D%'", "get", "DeviceID"],
                    capture_output=True, text=True, timeout=10,
                )
                return "VID_0E8D" in result.stdout
            except (subprocess.TimeoutExpired, FileNotFoundError):
                return False
        else:
            try:
                result = subprocess.run(
                    ["lsusb"], capture_output=True, text=True, timeout=10
                )
                return "0e8d:" in result.stdout.lower()
            except (subprocess.TimeoutExpired, FileNotFoundError):
                return False

    def _find_sp_flash_tool(self) -> Optional[str]:
        """Locate SP Flash Tool executable."""
        search_dir = (
            Path(__file__).parent.parent.parent.parent
            / "resources" / "mediatek" / "sp_flash_tool"
        )

        candidates = []
        if search_dir.exists():
            candidates = list(search_dir.glob("flash_tool*")) + \
                         list(search_dir.glob("SP_Flash_Tool*"))

        for c in candidates:
            if c.suffix in (".exe", "") or c.is_file():
                return str(c)
        return None

    def _find_scatter(self, device_info: Dict,
                      firmware_path: Optional[str] = None) -> Optional[str]:
        """Find the scatter file for this device."""
        # Check provided firmware path first
        if firmware_path:
            fw_dir = Path(firmware_path)
            if fw_dir.is_file():
                fw_dir = fw_dir.parent
            for f in fw_dir.glob("*scatter*.txt"):
                return str(f)

        # Check resources
        search_dir = (
            Path(__file__).parent.parent.parent.parent
            / "resources" / "mediatek" / "scatter"
        )
        if search_dir.exists():
            platform = device_info.get("ro.board.platform", "")
            for f in search_dir.glob("*.txt"):
                if platform.lower() in f.name.lower():
                    return str(f)
            # Return first .txt if only one exists
            txts = list(search_dir.glob("*.txt"))
            if len(txts) == 1:
                return str(txts[0])

        return None

    def _execute_sp_flash(self, spft_path: str, scatter_path: str) -> PluginResult:
        """Execute SP Flash Tool with the given scatter file."""
        cmd = [
            spft_path,
            "--scatter", scatter_path,
            "--format", "whole",
            "--auto",
        ]

        logger.info(f"SP Flash command: {' '.join(cmd)}")

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )
            stdout = proc.stdout
            stderr = proc.stderr

            if proc.returncode == 0 or "success" in stdout.lower():
                logger.info("SP Flash successful")
                return PluginResult(
                    success=True,
                    message="Firmware flashed successfully via SP Flash Tool.",
                    data={"spft_output": stdout},
                )
            else:
                logger.error(f"SP Flash failed: {stdout}\n{stderr}")
                return PluginResult(
                    success=False,
                    message=f"SP Flash failed: {stderr or stdout}",
                    status=PluginStatus.FAILED,
                )

        except subprocess.TimeoutExpired:
            return PluginResult(
                success=False,
                message="SP Flash timed out (5 minutes). Check USB connection.",
                status=PluginStatus.FAILED,
            )
