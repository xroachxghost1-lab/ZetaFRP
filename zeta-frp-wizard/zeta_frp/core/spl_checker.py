#!/usr/bin/env python3
"""
Zeta FRP Wizard — Security Patch Level Checker
===============================================
Parses Android Security Patch Level (SPL) dates and maps them
to known FRP bypass method availability windows.

ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
Unauthorised use, distribution, or reproduction is an act of war.
Copyright © 2026 Zeta Omniverse. All rights reserved.
"""

from datetime import datetime, date
from enum import Enum, auto
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass

from zeta_frp.utils.logger import get_logger

logger = get_logger(__name__)

class MethodCategory(Enum):
    """Categories of FRP bypass methods."""
    INTERACTIVE_TALKBACK = auto()   # TalkBack accessibility exploit
    INTERACTIVE_EMERGENCY = auto()  # Emergency dialer exploit
    INTERACTIVE_KEYBOARD = auto()   # Keyboard settings hijack
    ADB_USER_SETUP = auto()         # ADB user_setup_complete trick
    CVE_EXPLOIT = auto()            # Known CVE-based exploits
    ODIN_FLASH = auto()             # Samsung Odin combination firmware
    EDL_FLASH = auto()              # Qualcomm EDL mode flashing
    SP_FLASH = auto()               # MediaTek SP Flash Tool
    FASTBOOT_FLASH = auto()         # Generic fastboot flashing

@dataclass
class MethodAvailability:
    """Describes when a bypass method is usable."""
    category: MethodCategory
    name: str
    description: str
    min_sdk: int          # Minimum Android SDK level
    max_sdk: int          # Maximum Android SDK level (0 = no upper limit)
    patched_after_spl: Optional[date]  # SPL date after which method is patched
    requires_usb_debugging: bool
    requires_unlocked_bootloader: bool
    risk_level: str       # "low", "medium", "high", "critical"
    brands: List[str]     # Supported manufacturer list (empty = all)

class SPLChecker:
    """
    Security Patch Level to method availability mapper.

    Determines which FRP bypass methods are viable based on:
    - Device Security Patch Level date
    - Android SDK version
    - Manufacturer
    - USB debugging / bootloader state

    The database is kept up-to-date via auto-updater pulling from
    Android Security Bulletins and community reports.
    """

    # ------------------------------------------------------------------
    # Method Database — Updated July 2026
    # ------------------------------------------------------------------

    METHOD_DB: List[MethodAvailability] = [
        MethodAvailability(
            category=MethodCategory.INTERACTIVE_TALKBACK,
            name="TalkBack Accessibility Exploit",
            description="Use TalkBack voice assistant to bypass setup wizard and access Settings",
            min_sdk=23, max_sdk=33,
            patched_after_spl=date(2024, 3, 1),
            requires_usb_debugging=False,
            requires_unlocked_bootloader=False,
            risk_level="low",
            brands=["Samsung", "Xiaomi", "Oppo", "Vivo"],
        ),
        MethodAvailability(
            category=MethodCategory.INTERACTIVE_EMERGENCY,
            name="Emergency Dialer Exploit",
            description="Use emergency call dialer codes to access hidden settings menus",
            min_sdk=23, max_sdk=33,
            patched_after_spl=date(2024, 6, 1),
            requires_usb_debugging=False,
            requires_unlocked_bootloader=False,
            risk_level="low",
            brands=["Samsung", "LG", "Motorola"],
        ),
        MethodAvailability(
            category=MethodCategory.INTERACTIVE_KEYBOARD,
            name="Keyboard Settings Hijack",
            description="Exploit keyboard settings to launch browser/settings during setup",
            min_sdk=23, max_sdk=33,
            patched_after_spl=date(2024, 3, 1),
            requires_usb_debugging=False,
            requires_unlocked_bootloader=False,
            risk_level="low",
            brands=[],  # Universal
        ),
        MethodAvailability(
            category=MethodCategory.ADB_USER_SETUP,
            name="ADB user_setup_complete Bypass",
            description="Use ADB to set user_setup_complete=1 and launch Settings",
            min_sdk=21, max_sdk=0,
            patched_after_spl=None,  # Still works if USB debugging is enabled
            requires_usb_debugging=True,
            requires_unlocked_bootloader=False,
            risk_level="low",
            brands=[],  # Universal
        ),
        MethodAvailability(
            category=MethodCategory.CVE_EXPLOIT,
            name="CVE-2025-22414 FRP Alert Activity",
            description="Privilege escalation in FRP Bypass Alert Activity",
            min_sdk=31, max_sdk=34,
            patched_after_spl=date(2025, 3, 1),
            requires_usb_debugging=False,
            requires_unlocked_bootloader=False,
            risk_level="medium",
            brands=[],  # Universal
        ),
        MethodAvailability(
            category=MethodCategory.ODIN_FLASH,
            name="Samsung Odin Combination Firmware",
            description="Flash combination firmware via Odin/Download Mode to remove FRP",
            min_sdk=21, max_sdk=0,
            patched_after_spl=None,  # Always works with correct firmware
            requires_usb_debugging=False,
            requires_unlocked_bootloader=False,
            risk_level="high",
            brands=["Samsung"],
        ),
        MethodAvailability(
            category=MethodCategory.EDL_FLASH,
            name="Qualcomm EDL 9008 Mode Flash",
            description="Force EDL mode and flash patched boot image to enable ADB",
            min_sdk=21, max_sdk=0,
            patched_after_spl=None,
            requires_usb_debugging=False,
            requires_unlocked_bootloader=False,
            risk_level="critical",
            brands=["Xiaomi", "Oppo", "OnePlus", "Motorola", "LG", "ZTE"],
        ),
        MethodAvailability(
            category=MethodCategory.SP_FLASH,
            name="MediaTek SP Flash Tool",
            description="Flash firmware via MediaTek BROM mode using SP Flash Tool",
            min_sdk=21, max_sdk=0,
            patched_after_spl=None,
            requires_usb_debugging=False,
            requires_unlocked_bootloader=False,
            risk_level="critical",
            brands=["Xiaomi", "Oppo", "Vivo", "Realme", "Tecno", "Infinix"],
        ),
        MethodAvailability(
            category=MethodCategory.FASTBOOT_FLASH,
            name="Fastboot FRP Erase",
            description="Erase FRP/persist partition via Fastboot (requires unlocked bootloader)",
            min_sdk=21, max_sdk=0,
            patched_after_spl=None,
            requires_usb_debugging=False,
            requires_unlocked_bootloader=True,
            risk_level="high",
            brands=["Google", "Motorola", "OnePlus", "Nokia"],
        ),
    ]

    def __init__(self):
        self._custom_methods: List[MethodAvailability] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_available_methods(
        self,
        manufacturer: str,
        android_sdk: int,
        spl_date: Optional[datetime] = None,
        usb_debugging: bool = False,
        bootloader_unlocked: bool = False,
    ) -> List[Tuple[MethodAvailability, bool]]:
        """
        Get all methods with availability status for this device.

        Returns:
            List of (MethodAvailability, is_available) tuples,
            sorted by risk (lowest first).
        """
        all_methods = self.METHOD_DB + self._custom_methods
        results = []

        for method in all_methods:
            available = self._check_method(
                method, manufacturer, android_sdk, spl_date,
                usb_debugging, bootloader_unlocked,
            )
            results.append((method, available))

        # Sort: available first, then by risk level
        risk_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        results.sort(key=lambda x: (
            not x[1],  # Available first
            risk_order.get(x[0].risk_level, 99),
        ))
        return results

    def get_recommended_method(
        self,
        manufacturer: str,
        android_sdk: int,
        spl_date: Optional[datetime] = None,
        usb_debugging: bool = False,
        bootloader_unlocked: bool = False,
    ) -> Optional[MethodAvailability]:
        """
        Get the single best (lowest risk, available) method for this device.
        Returns None if no method is available.
        """
        available = self.get_available_methods(
            manufacturer, android_sdk, spl_date,
            usb_debugging, bootloader_unlocked,
        )
        for method, is_available in available:
            if is_available:
                return method
        return None

    def add_custom_method(self, method: MethodAvailability) -> None:
        """Register a custom/user-defined bypass method."""
        self._custom_methods.append(method)
        logger.info(f"Custom method added: {method.name}")

    def get_patch_info(self, method: MethodAvailability) -> str:
        """
        Get human-readable information about when/why a method was patched.
        """
        if method.patched_after_spl is None:
            return f"{method.name} has no known SPL-based patch. It should work on all firmware versions (subject to other requirements)."

        patch_date = method.patched_after_spl.strftime("%B %Y")
        return (
            f"{method.name} was patched by Google/Samsung in the {patch_date} "
            f"Security Patch Level update. Devices with SPL after "
            f"{method.patched_after_spl.strftime('%Y-%m-%d')} are NOT vulnerable."
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _check_method(
        self,
        method: MethodAvailability,
        manufacturer: str,
        sdk: int,
        spl_date: Optional[datetime],
        usb_debugging: bool,
        bootloader_unlocked: bool,
    ) -> bool:
        """Check if a method is available for the given device state."""

        # SDK range check
        if sdk > 0:
            if method.min_sdk > 0 and sdk < method.min_sdk:
                return False
            if method.max_sdk > 0 and sdk > method.max_sdk:
                return False

        # Brand check (empty list = all brands)
        if method.brands:
            man_lower = manufacturer.lower()
            brand_match = any(b.lower() in man_lower for b in method.brands)
            if not brand_match:
                return False

        # SPL patch check
        if method.patched_after_spl and spl_date:
            if spl_date.date() > method.patched_after_spl:
                return False

        # USB debugging requirement
        if method.requires_usb_debugging and not usb_debugging:
            return False

        # Bootloader requirement
        if method.requires_unlocked_bootloader and not bootloader_unlocked:
            return False

        return True
