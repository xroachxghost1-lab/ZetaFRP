#!/usr/bin/env python3
"""
Zeta FRP Wizard — MediaTek BROM Handler
=========================================
Low-level MediaTek BootROM protocol handler.

MediaTek BROM is accessible when the device is powered off.
The protocol allows reading/writing device memory before
the bootloader executes, enabling FRP partition manipulation.

ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
Unauthorised use, distribution, or reproduction is an act of war.
Copyright © 2026 Zeta Omniverse. All rights reserved.
"""

from typing import Optional, Dict

from zeta_frp.utils.logger import get_logger

logger = get_logger(__name__)

class BROMHandler:
    """
    MediaTek BootROM mode handler.

    BROM mode is entered automatically when the device is powered on
    with specific USB conditions. The SoC boots into a minimal ROM
    that accepts commands over USB before loading the preloader.

    Key operations in BROM mode:
    - Read/write device memory
    - Disable protection (SLA/DAA)
    - Load custom bootloader/DA (Download Agent)
    - Read device info (chip ID, secure state)
    """

    # Known MediaTek USB VIDs
    MTK_PRELOADER_VID = 0x0E8D
    MTK_PRELOADER_PIDS = [0x0003, 0x2000, 0x2001, 0x3000]
    MTK_BROM_VID = 0x0E8D
    MTK_BROM_PID = 0x0003

    def __init__(self):
        self._connected = False
        self._chip_info: Dict = {}

    def detect(self) -> bool:
        """
        Detect if a MediaTek device is in BROM mode.
        """
        import sys
        if sys.platform.startswith("win"):
            return self._detect_windows()
        else:
            return self._detect_unix()

    def _detect_windows(self) -> bool:
        import subprocess
        try:
            result = subprocess.run(
                ["wmic", "path", "Win32_PnPEntity", "where",
                 "DeviceID like '%VID_0E8D%'", "get", "DeviceID"],
                capture_output=True, text=True, timeout=10,
            )
            if "VID_0E8D" in result.stdout:
                self._connected = True
                logger.info("MediaTek BROM device detected (Windows)")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return False

    def _detect_unix(self) -> bool:
        import subprocess
        try:
            result = subprocess.run(
                ["lsusb"], capture_output=True, text=True, timeout=10
            )
            if "0e8d:" in result.stdout.lower():
                self._connected = True
                logger.info("MediaTek BROM device detected (Unix)")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return False

    def get_entry_instructions(self, device_model: str = "") -> str:
        """
        Return human-readable instructions for entering BROM mode.
        Device-specific when possible, generic otherwise.
        """
        base_instructions = (
            "=== Entering MediaTek BROM Mode ===\n\n"
            "Method 1 (Volume Keys):\n"
            "  1. Power off the device completely\n"
            "  2. Hold Volume Up + Volume Down simultaneously\n"
            "  3. While holding, connect USB cable to PC\n"
            "  4. Device Manager should show 'MediaTek USB Port' or 'MTK USB Port'\n\n"
            "Method 2 (Test Point):\n"
            "  1. Disconnect battery (if removable)\n"
            "  2. Locate test points on motherboard (search for '{device_model} test point')\n"
            "  3. Short test points with tweezers\n"
            "  4. Connect USB while test points are shorted\n"
            "  5. Release test points after 2 seconds\n\n"
            "Method 3 (Software):\n"
            "  - Use 'adb reboot autodloader' if device has ADB access\n"
            "  - Some custom recoveries can reboot to BROM\n\n"
            "After entering BROM, install MediaTek VCOM drivers if prompted.\n"
            "Windows may require disabling driver signature enforcement."
        )
        return base_instructions
