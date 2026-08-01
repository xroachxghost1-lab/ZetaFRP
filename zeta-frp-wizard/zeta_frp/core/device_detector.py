#!/usr/bin/env python3
"""
Zeta FRP Wizard — Device Detector
==================================
Multi-mode USB device scanner that detects Android devices
in all connection modes: ADB, Fastboot, Download Mode (Odin),
EDL (Qualcomm 9008), BROM (MediaTek), and Recovery.

ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
Unauthorised use, distribution, or reproduction is an act of war.
Copyright © 2026 Zeta Omniverse. All rights reserved.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, Dict
import subprocess
import sys

from zeta_frp.utils.logger import get_logger

logger = get_logger(__name__)

class DeviceMode(Enum):
    """Connection modes an Android device can be in."""
    ADB = auto()           # Normal boot with ADB enabled
    FASTBOOT = auto()      # Bootloader/Fastboot mode
    DOWNLOAD = auto()      # Samsung Download/Odin mode
    EDL = auto()           # Qualcomm Emergency Download Mode (9008)
    BROM = auto()          # MediaTek BootROM mode
    RECOVERY = auto()      # Stock/custom recovery
    SIDELOAD = auto()      # ADB sideload in recovery
    MTP = auto()           # Media Transfer Protocol (no ADB)
    UNKNOWN = auto()       # Device detected but mode unknown

@dataclass
class DetectedDevice:
    """Information about a detected Android device."""
    serial: str
    mode: DeviceMode
    manufacturer: str = ""
    model: str = ""
    product: str = ""
    android_version: str = ""
    security_patch: str = ""
    sdk_level: int = 0
    soc_manufacturer: str = ""  # Qualcomm, MediaTek, Exynos, etc.
    imei: str = ""
    transport: str = "usb"      # usb, tcpip
    raw_props: Dict[str, str] = field(default_factory=dict)

    @property
    def display_name(self) -> str:
        """Human-readable device identifier."""
        if self.manufacturer and self.model:
            return f"{self.manufacturer} {self.model} ({self.serial[:8]})"
        return self.serial

    @property
    def is_samsung(self) -> bool:
        return self.manufacturer.lower() == "samsung"

    @property
    def is_xiaomi(self) -> bool:
        return self.manufacturer.lower() in ("xiaomi", "redmi", "poco")

    @property
    def is_oppo(self) -> bool:
        return self.manufacturer.lower() in ("oppo", "realme", "oneplus")

    @property
    def is_vivo(self) -> bool:
        return self.manufacturer.lower() == "vivo"

    @property
    def is_qualcomm(self) -> bool:
        return "qualcomm" in self.soc_manufacturer.lower() or "qcom" in self.soc_manufacturer.lower()

    @property
    def is_mediatek(self) -> bool:
        return "mediatek" in self.soc_manufacturer.lower() or "mtk" in self.soc_manufacturer.lower()

class DeviceDetector:
    """
    Multi-mode device detector.

    Scans USB, ADB, and Fastboot to find connected Android devices
    and enrich them with detailed property information.
    """

    def __init__(self):
        self._devices: List[DetectedDevice] = []

    def scan(self) -> List[DetectedDevice]:
        """
        Perform a full scan for all connected Android devices.

        Returns:
            List of detected devices with enriched information.
        """
        self._devices = []
        self._scan_adb()
        self._scan_fastboot()
        self._scan_edl()
        self._scan_brom()
        self._enrich_devices()
        logger.info(f"Scan complete: {len(self._devices)} device(s) found")
        return self._devices

    # ------------------------------------------------------------------
    # Scanner Methods
    # ------------------------------------------------------------------

    def _scan_adb(self) -> None:
        """Scan for devices in ADB mode."""
        try:
            result = subprocess.run(
                ["adb", "devices", "-l"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                return

            for line in result.stdout.strip().split("\n")[1:]:
                if not line.strip():
                    continue
                parts = line.split()
                if len(parts) < 2:
                    continue

                serial = parts[0]
                state = parts[1]
                device = DetectedDevice(serial=serial, mode=self._state_to_mode(state))

                # Parse -l flags
                for part in parts[2:]:
                    if ":" in part:
                        key, val = part.split(":", 1)
                        if key == "model":
                            device.model = val.replace("_", " ")
                        elif key == "product":
                            device.product = val
                        elif key == "transport_id":
                            pass  # Internal ADB ID

                # Determine manufacturer from product
                device.manufacturer = self._guess_manufacturer(device.product, device.model)

                self._devices.append(device)
                logger.debug(f"ADB device found: {device.display_name} [{state}]")

        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.debug("ADB not available")

    def _scan_fastboot(self) -> None:
        """Scan for devices in Fastboot mode."""
        try:
            result = subprocess.run(
                ["fastboot", "devices", "-l"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                return

            for line in result.stdout.strip().split("\n"):
                if not line.strip() or "fastboot" not in line:
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    serial = parts[0]
                    # Check if already detected
                    if any(d.serial == serial for d in self._devices):
                        continue
                    device = DetectedDevice(serial=serial, mode=DeviceMode.FASTBOOT)
                    for part in parts[1:]:
                        if part.startswith("product:"):
                            device.product = part.split(":", 1)[1]
                    device.manufacturer = self._guess_manufacturer(device.product, "")
                    self._devices.append(device)
                    logger.debug(f"Fastboot device found: {serial}")

        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.debug("Fastboot not available")

    def _scan_edl(self) -> None:
        """
        Scan for Qualcomm EDL (9008) devices via USB VID/PID.
        Qualcomm EDL: VID=05C6, PID=9008
        """
        if sys.platform.startswith("win"):
            self._scan_edl_windows()
        else:
            self._scan_edl_unix()

    def _scan_edl_windows(self) -> None:
        """Windows-specific EDL detection via wmic."""
        try:
            result = subprocess.run(
                ["wmic", "path", "Win32_PnPEntity", "where",
                 "DeviceID like '%VID_05C6&PID_9008%'", "get", "DeviceID"],
                capture_output=True, text=True, timeout=10
            )
            if "VID_05C6" in result.stdout and "PID_9008" in result.stdout:
                device = DetectedDevice(
                    serial="EDL-9008",
                    mode=DeviceMode.EDL,
                    manufacturer="Qualcomm",
                    soc_manufacturer="Qualcomm",
                )
                self._devices.append(device)
                logger.debug("Qualcomm EDL device detected (9008 mode)")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    def _scan_edl_unix(self) -> None:
        """Unix EDL detection via lsusb."""
        try:
            result = subprocess.run(
                ["lsusb"], capture_output=True, text=True, timeout=10
            )
            if "05c6:9008" in result.stdout.lower():
                device = DetectedDevice(
                    serial="EDL-9008",
                    mode=DeviceMode.EDL,
                    manufacturer="Qualcomm",
                    soc_manufacturer="Qualcomm",
                )
                self._devices.append(device)
                logger.debug("Qualcomm EDL device detected (9008 mode)")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    def _scan_brom(self) -> None:
        """
        Scan for MediaTek BROM devices via USB VID/PID.
        MediaTek BROM: VID=0E8D, various PIDs (0003, 2000, 2001)
        """
        if sys.platform.startswith("win"):
            self._scan_brom_windows()
        else:
            self._scan_brom_unix()

    def _scan_brom_windows(self) -> None:
        try:
            result = subprocess.run(
                ["wmic", "path", "Win32_PnPEntity", "where",
                 "DeviceID like '%VID_0E8D%'", "get", "DeviceID"],
                capture_output=True, text=True, timeout=10
            )
            if "VID_0E8D" in result.stdout:
                device = DetectedDevice(
                    serial="BROM-MTK",
                    mode=DeviceMode.BROM,
                    manufacturer="MediaTek",
                    soc_manufacturer="MediaTek",
                )
                self._devices.append(device)
                logger.debug("MediaTek BROM device detected")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    def _scan_brom_unix(self) -> None:
        try:
            result = subprocess.run(
                ["lsusb"], capture_output=True, text=True, timeout=10
            )
            if "0e8d:" in result.stdout.lower():
                device = DetectedDevice(
                    serial="BROM-MTK",
                    mode=DeviceMode.BROM,
                    manufacturer="MediaTek",
                    soc_manufacturer="MediaTek",
                )
                self._devices.append(device)
                logger.debug("MediaTek BROM device detected")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    # ------------------------------------------------------------------
    # Device Enrichment
    # ------------------------------------------------------------------

    def _enrich_devices(self) -> None:
        """Enrich all detected devices with property data where possible."""
        for device in self._devices:
            if device.mode == DeviceMode.ADB:
                self._enrich_adb_device(device)
            elif device.mode == DeviceMode.FASTBOOT:
                self._enrich_fastboot_device(device)

    def _enrich_adb_device(self, device: DetectedDevice) -> None:
        """Pull properties from an ADB-connected device."""
        try:
            # Get all system properties
            result = subprocess.run(
                ["adb", "-s", device.serial, "shell", "getprop"],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                device.raw_props = {}
                for line in result.stdout.strip().split("\n"):
                    import re
                    match = re.match(r"\[(.+?)\]:\s*\[(.*?)\]", line)
                    if match:
                        device.raw_props[match.group(1)] = match.group(2)

                device.manufacturer = device.raw_props.get(
                    "ro.product.manufacturer", device.manufacturer
                )
                device.model = device.raw_props.get(
                    "ro.product.model", device.model
                )
                device.android_version = device.raw_props.get(
                    "ro.build.version.release", ""
                )
                device.sdk_level = int(device.raw_props.get(
                    "ro.build.version.sdk", 0
                ))
                # Security patch from vendor patch level (more accurate)
                device.security_patch = device.raw_props.get(
                    "ro.vendor.build.security_patch",
                    device.raw_props.get("ro.build.version.security_patch", "")
                )
                device.soc_manufacturer = device.raw_props.get(
                    "ro.board.platform", ""
                )

                # Map platform to SoC manufacturer
                plat = device.soc_manufacturer.lower()
                if any(x in plat for x in ("msm", "sdm", "sm", "qcom")):
                    device.soc_manufacturer = "Qualcomm"
                elif any(x in plat for x in ("mt", "mtk")):
                    device.soc_manufacturer = "MediaTek"
                elif "exynos" in plat:
                    device.soc_manufacturer = "Samsung Exynos"
                elif "gs" in plat or "tensor" in plat:
                    device.soc_manufacturer = "Google Tensor"

        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    def _enrich_fastboot_device(self, device: DetectedDevice) -> None:
        """Pull variables from a Fastboot-connected device."""
        try:
            result = subprocess.run(
                ["fastboot", "-s", device.serial, "getvar", "all"],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                import re
                for line in result.stdout.split("\n"):
                    match = re.match(r"\(bootloader\)\s*(\S+):\s*(.+)", line)
                    if match:
                        key, val = match.group(1), match.group(2).strip()
                        device.raw_props[key] = val
                        if key == "product":
                            device.product = val
                        elif key == "variant":
                            device.model = val

                device.manufacturer = device.raw_props.get(
                    "product", device.manufacturer
                )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _state_to_mode(state: str) -> DeviceMode:
        """Map ADB device state string to DeviceMode."""
        state_lower = state.lower()
        if state_lower == "device":
            return DeviceMode.ADB
        elif state_lower == "recovery":
            return DeviceMode.RECOVERY
        elif state_lower == "sideload":
            return DeviceMode.SIDELOAD
        elif state_lower == "unauthorized":
            return DeviceMode.ADB  # Still ADB, needs auth
        elif state_lower == "offline":
            return DeviceMode.UNKNOWN
        return DeviceMode.UNKNOWN

    @staticmethod
    def _guess_manufacturer(product: str, model: str) -> str:
        """Guess manufacturer from product/model codes."""
        combined = f"{product} {model}".lower()
        if "samsung" in combined or product.startswith(("SM-", "GT-", "SCH-")):
            return "Samsung"
        if any(x in combined for x in ("xiaomi", "redmi", "poco")):
            return "Xiaomi"
        if any(x in combined for x in ("oppo", "realme", "oneplus")):
            return "Oppo"
        if "vivo" in combined:
            return "Vivo"
        if any(x in combined for x in ("motorola", "moto")):
            return "Motorola"
        if any(x in combined for x in ("pixel", "sailfish", "marlin", "walleye",
                                        "taimen", "crosshatch", "blueline",
                                        "bonito", "sargo", "coral", "flame",
                                        "sunfish", "bramble", "redfin", "barbet",
                                        "oriole", "raven", "bluejay", "panther",
                                        "cheetah", "lynx", "tangorpro", "felix",
                                        "husky", "shiba", "akita", "tokay",
                                        "caiman", "komodo")):
            return "Google"
        if "huawei" in combined or product.startswith(("ANE-", "CLT-", "ELE-",
                                                         "VOG-", "LYA-", "TAS-")):
            return "Huawei"
        if "lg" in combined or product.startswith(("LM-", "LG-")):
            return "LG"
        return "Unknown"
