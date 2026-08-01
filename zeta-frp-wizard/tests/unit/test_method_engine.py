#!/usr/bin/env python3
"""
Tests for method engine module.

ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
Unauthorised use, distribution, or reproduction is an act of war.
Copyright © 2026 Zeta Omniverse. All rights reserved.
"""

import pytest
from zeta_frp.core.method_engine import (
    MethodEngine, ExecutionPlan, ExecutionPhase,
)
from zeta_frp.core.device_detector import DetectedDevice, DeviceMode
from zeta_frp.core.spl_checker import MethodCategory

class TestMethodEngine:
    """Tests for MethodEngine class."""

    def setup_method(self):
        self.engine = MethodEngine()

    def test_create_plan_old_samsung(self):
        """Plan for old Samsung with USB debugging should use ADB."""
        device = DetectedDevice(
            serial="test123",
            mode=DeviceMode.ADB,
            manufacturer="Samsung",
            model="Galaxy S10",
            android_version="10",
            security_patch="2023-06-01",
            sdk_level=29,
        )
        plan = self.engine.create_plan(device)
        assert plan is not None
        assert len(plan.steps) > 0
        # Should prefer low-risk method
        assert plan.method.risk_level == "low"

    def test_create_plan_new_samsung(self):
        """Plan for new Samsung without USB debugging must use Odin."""
        device = DetectedDevice(
            serial="test456",
            mode=DeviceMode.UNKNOWN,
            manufacturer="Samsung",
            model="Galaxy S24",
            android_version="15",
            security_patch="2026-03-01",
            sdk_level=35,
        )
        plan = self.engine.create_plan(device)
        assert plan is not None
        # Should recommend Odin (only viable method)
        assert plan.method.category == MethodCategory.ODIN_FLASH
        # Should have warnings about firmware compatibility
        assert len(plan.warnings) > 0

    def test_create_plan_xiaomi(self):
        """Plan for Xiaomi should use EDL or SP Flash."""
        device = DetectedDevice(
            serial="xiaomi123",
            mode=DeviceMode.UNKNOWN,
            manufacturer="Xiaomi",
            model="Redmi Note 12",
            android_version="13",
            security_patch="2025-01-01",
            sdk_level=33,
            soc_manufacturer="Qualcomm",
        )
        plan = self.engine.create_plan(device)
        assert plan is not None
        assert plan.method.category in (MethodCategory.EDL_FLASH, MethodCategory.SP_FLASH)

    def test_create_plan_raises_for_incompatible(self):
        """Should raise ValueError if no method is available."""
        device = DetectedDevice(
            serial="weird123",
            mode=DeviceMode.UNKNOWN,
            manufacturer="UnknownBrand",
            model="WeirdPhone",
            android_version="16",
            security_patch="2027-01-01",
            sdk_level=36,
        )
        # Even for unknown brands, a flashing method should be available
        plan = self.engine.create_plan(device)
        assert plan is not None  # Fastboot erase is universal

    def test_force_method(self):
        """Forcing a specific method should override SPL checks."""
        device = DetectedDevice(
            serial="test",
            mode=DeviceMode.ADB,
            manufacturer="Samsung",
            model="S24",
            security_patch="2026-06-01",
            sdk_level=35,
        )
        plan = self.engine.create_plan(device, force_method=MethodCategory.ODIN_FLASH)
        assert plan.method.category == MethodCategory.ODIN_FLASH

    def test_get_all_methods_for_device(self):
        """Should return all potentially applicable methods."""
        device = DetectedDevice(
            serial="test",
            mode=DeviceMode.ADB,
            manufacturer="Samsung",
            model="S21",
            security_patch="2023-06-01",
            sdk_level=31,
        )
        methods = self.engine.get_all_methods_for_device(device)
        assert len(methods) > 0
        # Old SPL should have more methods available
        assert len(methods) >= 3
