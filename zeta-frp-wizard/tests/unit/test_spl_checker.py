#!/usr/bin/env python3
"""
Tests for SPL checker module.

ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
Unauthorised use, distribution, or reproduction is an act of war.
Copyright © 2026 Zeta Omniverse. All rights reserved.
"""

import pytest
from datetime import datetime, date
from zeta_frp.core.spl_checker import (
    SPLChecker, MethodAvailability, MethodCategory,
)

class TestSPLChecker:
    """Tests for SPLChecker class."""

    def setup_method(self):
        self.checker = SPLChecker()

    def test_old_device_has_interactive_methods(self):
        """Device with SPL before March 2024 should have TalkBack available."""
        methods = self.checker.get_available_methods(
            manufacturer="Samsung",
            android_sdk=31,  # Android 12
            spl_date=datetime(2023, 6, 1),
            usb_debugging=False,
        )
        available = [m for m, ok in methods if ok]
        categories = [m.category for m in available]
        assert MethodCategory.INTERACTIVE_TALKBACK in categories

    def test_new_device_no_interactive_methods(self):
        """Device with recent SPL should NOT have TalkBack available."""
        methods = self.checker.get_available_methods(
            manufacturer="Samsung",
            android_sdk=34,  # Android 14
            spl_date=datetime(2025, 6, 1),
            usb_debugging=False,
        )
        available = [m for m, ok in methods if ok]
        categories = [m.category for m in available]
        assert MethodCategory.INTERACTIVE_TALKBACK not in categories

    def test_odin_always_available_for_samsung(self):
        """Odin method should always be available for Samsung devices."""
        methods = self.checker.get_available_methods(
            manufacturer="Samsung",
            android_sdk=35,  # Android 15
            spl_date=datetime(2026, 6, 1),
            usb_debugging=False,
        )
        available = [m for m, ok in methods if ok]
        categories = [m.category for m in available]
        assert MethodCategory.ODIN_FLASH in categories

    def test_adb_requires_usb_debugging(self):
        """ADB method should require USB debugging."""
        methods = self.checker.get_available_methods(
            manufacturer="Samsung",
            android_sdk=31,
            spl_date=datetime(2023, 1, 1),
            usb_debugging=False,
        )
        available = [m for m, ok in methods if ok]
        categories = [m.category for m in available]
        assert MethodCategory.ADB_USER_SETUP not in categories

        methods_with_debug = self.checker.get_available_methods(
            manufacturer="Samsung",
            android_sdk=31,
            spl_date=datetime(2023, 1, 1),
            usb_debugging=True,
        )
        available_with = [m for m, ok in methods_with_debug if ok]
        categories_with = [m.category for m in available_with]
        assert MethodCategory.ADB_USER_SETUP in categories_with

    def test_edl_only_for_qualcomm_brands(self):
        """EDL should only appear for Qualcomm-compatible brands."""
        methods = self.checker.get_available_methods(
            manufacturer="Xiaomi",
            android_sdk=31,
            spl_date=datetime(2024, 1, 1),
        )
        available = [m for m, ok in methods if ok]
        categories = [m.category for m in available]
        assert MethodCategory.EDL_FLASH in categories

    def test_sp_flash_for_mediatek_brands(self):
        """SP Flash should appear for MediaTek-compatible brands."""
        methods = self.checker.get_available_methods(
            manufacturer="Vivo",
            android_sdk=31,
            spl_date=datetime(2024, 1, 1),
        )
        available = [m for m, ok in methods if ok]
        categories = [m.category for m in available]
        assert MethodCategory.SP_FLASH in categories

    def test_recommended_method_old_device(self):
        """Recommended method for old Samsung should be low-risk interactive."""
        method = self.checker.get_recommended_method(
            manufacturer="Samsung",
            android_sdk=31,
            spl_date=datetime(2023, 6, 1),
        )
        assert method is not None
        assert method.risk_level == "low"

    def test_recommended_method_new_device(self):
        """Recommended method for new Samsung should be Odin (only option)."""
        method = self.checker.get_recommended_method(
            manufacturer="Samsung",
            android_sdk=34,
            spl_date=datetime(2025, 6, 1),
        )
        assert method is not None
        assert method.category == MethodCategory.ODIN_FLASH

    def test_get_patch_info(self):
        """Patch info should include the SPL date."""
        method = self.checker.METHOD_DB[0]  # TalkBack
        info = self.checker.get_patch_info(method)
        assert "March 2024" in info
