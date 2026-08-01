#!/usr/bin/env python3
"""
Zeta FRP Wizard — Plugin Base Class
=====================================
Abstract base for all bypass plugins. Each plugin handles
a specific brand + SoC combination.

ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
Unauthorised use, distribution, or reproduction is an act of war.
Copyright © 2026 Zeta Omniverse. All rights reserved.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum, auto

from zeta_frp.utils.logger import get_logger

logger = get_logger(__name__)

class PluginStatus(Enum):
    """Status of a plugin operation."""
    READY = auto()
    RUNNING = auto()
    SUCCESS = auto()
    FAILED = auto()
    CANCELLED = auto()

@dataclass
class PluginResult:
    """Result from a plugin operation."""
    success: bool
    message: str = ""
    data: Dict = field(default_factory=dict)
    status: PluginStatus = PluginStatus.READY

class FRPBypassPlugin(ABC):
    """
    Abstract base class for all FRP bypass plugins.

    Subclasses must implement:
    - plugin_name
    - supported_brands
    - supported_socs
    - check_compatibility()
    - execute_bypass()

    Optional overrides:
    - pre_flight_checks()
    - post_bypass_cleanup()
    - get_required_files()
    """

    # ------------------------------------------------------------------
    # Subclass Must Define
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def plugin_name(self) -> str:
        """Human-readable plugin name."""
        ...

    @property
    @abstractmethod
    def plugin_version(self) -> str:
        """Plugin version string."""
        ...

    @property
    @abstractmethod
    def supported_brands(self) -> List[str]:
        """List of supported manufacturer names (lowercase)."""
        ...

    @property
    @abstractmethod
    def supported_socs(self) -> List[str]:
        """
        List of supported SoC platforms.
        Examples: 'qualcomm', 'mediatek', 'exynos', 'tensor'
        Empty list = all SoCs.
        """
        ...

    # ------------------------------------------------------------------
    # Abstract Methods
    # ------------------------------------------------------------------

    @abstractmethod
    def check_compatibility(self, device_info: Dict) -> PluginResult:
        """
        Check if this plugin is compatible with the connected device.

        Args:
            device_info: Device properties dict from DeviceInfoReader.

        Returns:
            PluginResult with success=True if compatible.
        """
        ...

    @abstractmethod
    def execute_bypass(self, device_info: Dict,
                       firmware_path: Optional[str] = None,
                       progress_callback=None) -> PluginResult:
        """
        Execute the FRP bypass for this device.

        Args:
            device_info: Device properties dict.
            firmware_path: Optional path to firmware file for flashing.
            progress_callback: Optional callable(percent: int, message: str)
                               for progress reporting.

        Returns:
            PluginResult indicating success/failure.
        """
        ...

    # ------------------------------------------------------------------
    # Optional Overrides
    # ------------------------------------------------------------------

    def pre_flight_checks(self, device_info: Dict) -> List[str]:
        """
        Run pre-flight checks. Return list of warnings/issues.
        Empty list = all checks passed.
        """
        return []

    def post_bypass_cleanup(self, device_info: Dict) -> PluginResult:
        """Run cleanup after bypass (e.g., re-lock bootloader, flash stock)."""
        return PluginResult(success=True, message="No cleanup needed")

    def get_required_files(self, device_info: Dict) -> List[str]:
        """
        Return list of required files that the user must provide
        or the tool must download.
        """
        return []

    # ------------------------------------------------------------------
    # Common Helpers
    # ------------------------------------------------------------------

    def _check_brand(self, device_info: Dict) -> bool:
        """Check if device brand matches supported brands."""
        if not self.supported_brands:
            return True  # All brands supported
        manufacturer = device_info.get("ro.product.manufacturer", "").lower()
        return any(brand in manufacturer for brand in self.supported_brands)

    def _check_soc(self, device_info: Dict) -> bool:
        """Check if device SoC matches supported SoCs."""
        if not self.supported_socs:
            return True  # All SoCs supported
        platform = device_info.get("ro.board.platform", "").lower()
        for soc in self.supported_socs:
            if soc == "qualcomm" and any(x in platform for x in ("msm", "sdm", "sm", "qcom")):
                return True
            if soc == "mediatek" and any(x in platform for x in ("mt", "mtk")):
                return True
            if soc == "exynos" and "exynos" in platform:
                return True
            if soc in platform:
                return True
        return False

    def _run_adb(self, command: str, serial: Optional[str] = None,
                 timeout: int = 15) -> PluginResult:
        """Run an ADB command and return a PluginResult."""
        from zeta_frp.utils.adb_wrapper import ADBWrapper
        adb = ADBWrapper()
        result = adb.shell(command, serial=serial, timeout=timeout)
        return PluginResult(
            success=result.success,
            message=result.stdout if result.success else result.stderr,
            status=PluginStatus.SUCCESS if result.success else PluginStatus.FAILED,
        )
