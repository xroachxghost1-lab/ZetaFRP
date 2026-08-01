#!/usr/bin/env python3
"""
Integration tests for plugin loading and method selection.

ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
Unauthorised use, distribution, or reproduction is an act of war.
Copyright © 2026 Zeta Omniverse. All rights reserved.
"""

import pytest
from zeta_frp.plugins.base import FRPBypassPlugin, PluginResult
from zeta_frp.plugins.samsung.odin_flasher import SamsungOdinPlugin
from zeta_frp.plugins.samsung.adb_samsung import SamsungADBBypass
from zeta_frp.plugins.qualcomm.edl_flasher import QualcommEDLPlugin
from zeta_frp.plugins.mediatek.sp_flasher import MediaTekSPFlashPlugin
from zeta_frp.plugins.universal.adb_bypass import UniversalADBBypass

class TestPluginLoading:
    """Test that all plugins load correctly and implement the interface."""

    PLUGIN_CLASSES = [
        SamsungOdinPlugin,
        QualcommEDLPlugin,
        MediaTekSPFlashPlugin,
        UniversalADBBypass,
    ]

    @pytest.mark.parametrize("plugin_cls", PLUGIN_CLASSES)
    def test_plugin_implements_interface(self, plugin_cls):
        """Every plugin must implement the FRPBypassPlugin interface."""
        plugin = plugin_cls()
        assert isinstance(plugin, FRPBypassPlugin)
        assert plugin.plugin_name
        assert plugin.plugin_version
        assert isinstance(plugin.supported_brands, list)
        assert isinstance(plugin.supported_socs, list)

    @pytest.mark.parametrize("plugin_cls", PLUGIN_CLASSES)
    def test_plugin_check_compatibility(self, plugin_cls):
        """check_compatibility should return a PluginResult."""
        plugin = plugin_cls()
        result = plugin.check_compatibility({
            "ro.product.manufacturer": "Samsung",
            "ro.product.model": "SM-G991B",
            "ro.board.platform": "exynos2100",
            "ro.build.version.sdk": "31",
        })
        assert isinstance(result, PluginResult)

    def test_samsung_plugin_accepts_samsung(self):
        plugin = SamsungOdinPlugin()
        result = plugin.check_compatibility({
            "ro.product.manufacturer": "Samsung",
            "ro.product.model": "SM-G991B",
        })
        assert result.success

    def test_samsung_plugin_rejects_non_samsung(self):
        plugin = SamsungOdinPlugin()
        result = plugin.check_compatibility({
            "ro.product.manufacturer": "Xiaomi",
            "ro.product.model": "Redmi Note 12",
        })
        assert not result.success

    def test_universal_adb_accepts_all(self):
        plugin = UniversalADBBypass()
        result = plugin.check_compatibility({
            "ro.product.manufacturer": "AnyBrand",
            "ro.build.version.sdk": "31",
        })
        assert result.success

    def test_plugin_pre_flight_returns_list(self):
        """pre_flight_checks should return a list of warnings."""
        for plugin_cls in self.PLUGIN_CLASSES:
            plugin = plugin_cls()
            warnings = plugin.pre_flight_checks({
                "ro.product.manufacturer": "Samsung",
                "ro.product.model": "SM-G991B",
            })
            assert isinstance(warnings, list)

    def test_plugin_required_files_returns_list(self):
        """get_required_files should return a list."""
        for plugin_cls in self.PLUGIN_CLASSES:
            plugin = plugin_cls()
            files = plugin.get_required_files({
                "ro.product.model": "Test",
            })
            assert isinstance(files, list)
