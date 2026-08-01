#!/usr/bin/env python3
"""
Tests for device detector module.

ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
Unauthorised use, distribution, or reproduction is an act of war.
Copyright © 2026 Zeta Omniverse. All rights reserved.
"""

import pytest
from unittest.mock import patch, MagicMock
from zeta_frp.core.device_detector import (
    DeviceDetector, DetectedDevice, DeviceMode,
)

class TestDeviceDetector:
    """Tests for DeviceDetector class."""

    def test_init(self):
        detector = DeviceDetector()
        assert detector is not None
        assert detector._devices == []

    def test_scan_no_devices(self):
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            detector = DeviceDetector()
            devices = detector.scan()
            assert devices == []

    def test_state_to_mode(self):
        assert DeviceDetector._state_to_mode("device") == DeviceMode.ADB
        assert DeviceDetector._state_to_mode("recovery") == DeviceMode.RECOVERY
        assert DeviceDetector._state_to_mode("sideload") == DeviceMode.SIDELOAD
        assert DeviceDetector._state_to_mode("unauthorized") == DeviceMode.ADB
        assert DeviceDetector._state_to_mode("offline") == DeviceMode.UNKNOWN
        assert DeviceDetector._state_to_mode("unknown") == DeviceMode.UNKNOWN

    def test_guess_manufacturer_samsung(self):
        result = DeviceDetector._guess_manufacturer("SM-G991B", "")
        assert result == "Samsung"

    def test_guess_manufacturer_xiaomi(self):
        result = DeviceDetector._guess_manufacturer("", "Redmi Note 12")
        assert result == "Xiaomi"

    def test_guess_manufacturer_google(self):
        result = DeviceDetector._guess_manufacturer("oriole", "")
        assert result == "Google"

    def test_guess_manufacturer_unknown(self):
        result = DeviceDetector._guess_manufacturer("unknown_device", "")
        assert result == "Unknown"

class TestDetectedDevice:
    """Tests for DetectedDevice dataclass."""

    def test_display_name(self):
        device = DetectedDevice(
            serial="abc123def456",
            mode=DeviceMode.ADB,
            manufacturer="Samsung",
            model="Galaxy S21",
        )
        assert "Samsung Galaxy S21" in device.display_name
        assert "abc123de" in device.display_name

    def test_brand_checks(self):
        samsung = DetectedDevice(
            serial="x", mode=DeviceMode.ADB, manufacturer="Samsung"
        )
        assert samsung.is_samsung
        assert not samsung.is_xiaomi

        xiaomi = DetectedDevice(
            serial="x", mode=DeviceMode.ADB, manufacturer="Xiaomi"
        )
        assert xiaomi.is_xiaomi
        assert not xiaomi.is_samsung

    def test_soc_checks(self):
        qcom = DetectedDevice(
            serial="x", mode=DeviceMode.ADB, soc_manufacturer="Qualcomm"
        )
        assert qcom.is_qualcomm
        assert not qcom.is_mediatek

        mtk = DetectedDevice(
            serial="x", mode=DeviceMode.ADB, soc_manufacturer="MediaTek"
        )
        assert mtk.is_mediatek
        assert not mtk.is_qualcomm
