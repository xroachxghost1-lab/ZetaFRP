#!/usr/bin/env python3
"""
Tests for ADB wrapper module.

ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
Unauthorised use, distribution, or reproduction is an act of war.
Copyright © 2026 Zeta Omniverse. All rights reserved.
"""

import pytest
from unittest.mock import patch, MagicMock
from zeta_frp.utils.adb_wrapper import ADBWrapper, ADBResult, ADBDevice

class TestADBWrapper:
    """Tests for ADBWrapper class."""

    def test_init_default(self):
        adb = ADBWrapper()
        assert adb._port == 5037
        assert adb._adb_path is not None

    def test_init_custom(self):
        adb = ADBWrapper(adb_path="/custom/adb", port=9999)
        assert adb._adb_path == "/custom/adb"
        assert adb._port == 9999

    def test_find_adb_uses_env(self):
        with patch.dict("os.environ", {"ADB_PATH": "/env/adb"}):
            with patch("pathlib.Path.exists", return_value=True):
                adb = ADBWrapper()
                assert adb._adb_path == "/env/adb"

    @patch("subprocess.run")
    def test_list_devices_empty(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout="List of devices attached\n", stderr=""
        )
        adb = ADBWrapper()
        devices = adb.list_devices()
        assert devices == []

    @patch("subprocess.run")
    def test_list_devices_with_device(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="List of devices attached\nabc123  device product:test_model model:Test_Phone\n",
            stderr="",
        )
        adb = ADBWrapper()
        devices = adb.list_devices()
        assert len(devices) == 1
        assert devices[0].serial == "abc123"
        assert devices[0].state == "device"
        assert devices[0].model == "Test Phone"

    @patch("subprocess.run")
    def test_shell_success(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout="test output", stderr=""
        )
        adb = ADBWrapper()
        result = adb.shell("echo test")
        assert result.success
        assert result.stdout == "test output"

    @patch("subprocess.run")
    def test_shell_timeout(self, mock_run):
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="adb", timeout=5)
        adb = ADBWrapper()
        result = adb.shell("sleep 100", timeout=1)
        assert not result.success
        assert "timed out" in result.stderr.lower()

    @patch("subprocess.run")
    def test_bypass_frp_adb(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout="done", stderr=""
        )
        adb = ADBWrapper()
        result = adb.bypass_frp_adb(serial="test")
        assert result.success

    def test_get_prop_empty(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="", stderr=""
            )
            adb = ADBWrapper()
            result = adb.get_prop("nonexistent")
            assert result == ""
