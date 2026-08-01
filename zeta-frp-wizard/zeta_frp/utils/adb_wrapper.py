#!/usr/bin/env python3
"""
Zeta FRP Wizard — ADB Wrapper (Bare-Level Implementation)
==========================================================
Pure subprocess-based ADB client. No external dependencies beyond
the Android Debug Bridge binary. Implements the full ADB command
set needed for FRP bypass operations.

Protocol reference: https://android.googlesource.com/platform/packages/modules/adb/

ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
Unauthorised use, distribution, or reproduction is an act of war.
Copyright © 2026 Zeta Omniverse. All rights reserved.
"""

import subprocess
import os
import time
import re
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, field

from zeta_frp.utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class ADBDevice:
    """Represents a connected ADB device."""
    serial: str
    state: str  # "device", "offline", "unauthorized", "recovery", "sideload"
    model: str = ""
    product: str = ""
    transport_id: int = 0

@dataclass
class ADBResult:
    """Result of an ADB command execution."""
    success: bool
    stdout: str = ""
    stderr: str = ""
    returncode: int = -1
    command: str = ""

class ADBWrapper:
    """
    Bare-level ADB client wrapping the Android Debug Bridge binary.

    All operations are synchronous and use subprocess calls.
    Handles ADB server lifecycle, device authorization, and
    command retry logic.

    Usage:
        adb = ADBWrapper()
        adb.start_server()
        devices = adb.list_devices()
        if devices:
            result = adb.shell("settings get secure android_id")
    """

    DEFAULT_PORT = 5037
    DEFAULT_TIMEOUT = 15
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0

    def __init__(self, adb_path: Optional[str] = None, port: int = DEFAULT_PORT):
        self._adb_path = adb_path or self._find_adb()
        self._port = port
        self._server_started = False

    # ------------------------------------------------------------------
    # Server Management
    # ------------------------------------------------------------------

    def _find_adb(self) -> str:
        """Locate the ADB binary: bundled > environment > system PATH."""
        # Check bundled
        base = Path(__file__).parent.parent.parent / "resources" / "adb"
        candidates = []
        if os.name == "nt":
            candidates = [base / "adb.exe", Path("resources/adb/adb.exe")]
        else:
            candidates = [base / "adb", Path("resources/adb/adb")]

        for candidate in candidates:
            if candidate.exists():
                logger.debug(f"Using bundled ADB: {candidate}")
                return str(candidate)

        # Check environment variable
        env_path = os.environ.get("ADB_PATH")
        if env_path and Path(env_path).exists():
            return env_path

        # Check system PATH
        import shutil
        system_adb = shutil.which("adb")
        if system_adb:
            return system_adb

        # Fallback to "adb" and hope it's on PATH
        logger.warning("ADB not found in bundled location or PATH. Using 'adb' as fallback.")
        return "adb"

    def start_server(self) -> ADBResult:
        """Start the ADB server daemon."""
        result = self._run_adb(["start-server"], timeout=10)
        if result.success:
            self._server_started = True
            logger.info("ADB server started")
        return result

    def kill_server(self) -> ADBResult:
        """Stop the ADB server daemon."""
        result = self._run_adb(["kill-server"], timeout=10)
        self._server_started = False
        return result

    def restart_server(self) -> ADBResult:
        """Restart the ADB server."""
        self.kill_server()
        time.sleep(0.5)
        return self.start_server()

    def is_server_running(self) -> bool:
        """Check if ADB server is currently running."""
        result = self._run_adb(["devices"], timeout=5)
        return result.success and "daemon" not in result.stderr.lower()

    # ------------------------------------------------------------------
    # Device Discovery
    # ------------------------------------------------------------------

    def list_devices(self) -> List[ADBDevice]:
        """List all connected ADB devices with their state."""
        result = self._run_adb(["devices", "-l"], timeout=10)
        if not result.success:
            return []

        devices = []
        for line in result.stdout.strip().split("\n")[1:]:  # Skip header
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 2:
                device = ADBDevice(serial=parts[0], state=parts[1])
                # Parse -l flags
                for part in parts[2:]:
                    if part.startswith("model:"):
                        device.model = part.split(":", 1)[1]
                    elif part.startswith("product:"):
                        device.product = part.split(":", 1)[1]
                    elif part.startswith("transport_id:"):
                        device.transport_id = int(part.split(":", 1)[1])
                devices.append(device)

        logger.debug(f"Found {len(devices)} ADB device(s)")
        return devices

    def get_device(self, serial: Optional[str] = None) -> Optional[ADBDevice]:
        """Get a specific device by serial, or the first available device."""
        devices = self.list_devices()
        if not devices:
            return None
        if serial:
            for d in devices:
                if d.serial == serial:
                    return d
            return None
        # Return first "device" state device
        for d in devices:
            if d.state == "device":
                return d
        return devices[0]

    def wait_for_device(self, serial: Optional[str] = None, timeout: int = 60) -> bool:
        """Wait for a device to be connected and authorized."""
        cmd = ["wait-for-device"]
        if serial:
            cmd = ["-s", serial, "wait-for-device"]
        result = self._run_adb(cmd, timeout=timeout)
        return result.success

    # ------------------------------------------------------------------
    # Shell Commands
    # ------------------------------------------------------------------

    def shell(self, command: str, serial: Optional[str] = None,
              timeout: int = DEFAULT_TIMEOUT, root: bool = False) -> ADBResult:
        """
        Execute a shell command on the device.

        Args:
            command: The shell command to run.
            serial: Target device serial, or None for default.
            timeout: Command timeout in seconds.
            root: If True, attempt to run as root (requires rooted device).
        """
        cmd = self._build_device_cmd(["shell"], serial)
        if root:
            cmd.append("su -c")
        cmd.append(command)
        return self._run_adb(cmd, timeout=timeout)

    def shell_su(self, command: str, serial: Optional[str] = None,
                 timeout: int = DEFAULT_TIMEOUT) -> ADBResult:
        """Execute a shell command with superuser privileges."""
        return self.shell(f"su -c '{command}'", serial=serial, timeout=timeout)

    # ------------------------------------------------------------------
    # File Operations
    # ------------------------------------------------------------------

    def push(self, local: str, remote: str, serial: Optional[str] = None,
             timeout: int = 60) -> ADBResult:
        """Push a file from the host to the device."""
        cmd = self._build_device_cmd(["push", local, remote], serial)
        return self._run_adb(cmd, timeout=timeout)

    def pull(self, remote: str, local: str, serial: Optional[str] = None,
             timeout: int = 60) -> ADBResult:
        """Pull a file from the device to the host."""
        cmd = self._build_device_cmd(["pull", remote, local], serial)
        return self._run_adb(cmd, timeout=timeout)

    def install(self, apk_path: str, serial: Optional[str] = None,
                timeout: int = 120, replace: bool = True,
                grant_permissions: bool = True) -> ADBResult:
        """Install an APK on the device."""
        flags = []
        if replace:
            flags.append("-r")
        if grant_permissions:
            flags.append("-g")
        cmd = self._build_device_cmd(["install"] + flags + [apk_path], serial)
        return self._run_adb(cmd, timeout=timeout)

    # ------------------------------------------------------------------
    # System Operations
    # ------------------------------------------------------------------

    def reboot(self, target: str = "", serial: Optional[str] = None,
               timeout: int = 30) -> ADBResult:
        """
        Reboot the device. Target can be:
        "" (system), "bootloader", "recovery", "fastboot", "edl"
        """
        cmd = self._build_device_cmd(["reboot"], serial)
        if target:
            cmd.append(target)
        return self._run_adb(cmd, timeout=timeout)

    def root(self, serial: Optional[str] = None) -> ADBResult:
        """Restart adbd with root permissions."""
        cmd = self._build_device_cmd(["root"], serial)
        return self._run_adb(cmd, timeout=10)

    def remount(self, serial: Optional[str] = None) -> ADBResult:
        """Remount partitions as read-write (requires root)."""
        cmd = self._build_device_cmd(["remount"], serial)
        return self._run_adb(cmd, timeout=30)

    # ------------------------------------------------------------------
    # FRP-Specific Operations
    # ------------------------------------------------------------------

    def get_prop(self, prop: str, serial: Optional[str] = None) -> str:
        """Get a system property value."""
        result = self.shell(f"getprop {prop}", serial=serial)
        if result.success:
            return result.stdout.strip()
        return ""

    def get_all_props(self, serial: Optional[str] = None) -> Dict[str, str]:
        """Get all system properties as a dictionary."""
        result = self.shell("getprop", serial=serial, timeout=20)
        props = {}
        if result.success:
            for line in result.stdout.strip().split("\n"):
                match = re.match(r"\[(.+?)\]:\s*\[(.*?)\]", line)
                if match:
                    props[match.group(1)] = match.group(2)
        return props

    def get_imei(self, serial: Optional[str] = None) -> str:
        """Get device IMEI (requires phone permission on Android 10+)."""
        result = self.shell("service call iphonesubinfo 1", serial=serial)
        if result.success:
            # Parse the service call output for IMEI
            match = re.search(r"'([0-9]{15})'", result.stdout)
            if match:
                return match.group(1)
        # Fallback: try dumpsys
        result = self.shell("dumpsys iphonesubinfo", serial=serial)
        if result.success:
            match = re.search(r"Device ID[=:]\s*([0-9]{15})", result.stdout)
            if match:
                return match.group(1)
        return ""

    def bypass_frp_adb(self, serial: Optional[str] = None) -> ADBResult:
        """
        Execute the canonical ADB FRP bypass:
        1. Set user_setup_complete = 1
        2. Launch Settings
        3. (Optional) Remove Google account entries
        """
        commands = [
            "content insert --uri content://settings/secure --bind name:s:user_setup_complete --bind value:i:1",
            "content insert --uri content://settings/global --bind name:s:device_provisioned --bind value:i:1",
            "am start -n com.android.settings/.Settings",
        ]
        results = []
        for cmd in commands:
            r = self.shell(cmd, serial=serial)
            results.append(r)
            if not r.success:
                logger.warning(f"ADB FRP command failed: {cmd}")
            time.sleep(0.5)

        all_ok = all(r.success for r in results)
        return ADBResult(
            success=all_ok,
            stdout="\n".join(r.stdout for r in results),
            stderr="\n".join(r.stderr for r in results),
            command="; ".join(commands),
        )

    def remove_google_accounts(self, serial: Optional[str] = None) -> ADBResult:
        """Remove all Google accounts from the device via content provider."""
        cmd = (
            "content delete --uri content://com.android.contacts/data/"
            " --where \"account_type='com.google'\""
        )
        return self.shell(cmd, serial=serial)

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _build_device_cmd(self, base_cmd: List[str],
                          serial: Optional[str] = None) -> List[str]:
        """Build the full command list with optional device specifier."""
        cmd = [self._adb_path]
        if serial:
            cmd.extend(["-s", serial])
        cmd.extend(base_cmd)
        return cmd

    def _run_adb(self, cmd: List[str], timeout: int = DEFAULT_TIMEOUT,
                 retries: int = 0) -> ADBResult:
        """
        Execute an ADB command with retry logic.

        Automatically handles server-not-started errors by launching
        the server and retrying.
        """
        cmd_str = " ".join(cmd)
        logger.debug(f"ADB: {cmd_str}")

        for attempt in range(self.MAX_RETRIES if retries == 0 else retries + 1):
            try:
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    env={**os.environ, "ADB_VENDOR_KEYS": "1"},
                )
                stdout = proc.stdout.strip()
                stderr = proc.stderr.strip()

                if proc.returncode == 0:
                    logger.debug(f"ADB OK: {cmd_str}")
                    return ADBResult(
                        success=True,
                        stdout=stdout,
                        stderr=stderr,
                        returncode=proc.returncode,
                        command=cmd_str,
                    )

                # Handle server not running
                if "daemon" in stderr.lower() and "not running" in stderr.lower():
                    logger.debug("ADB daemon not running — starting server")
                    self.start_server()
                    time.sleep(self.RETRY_DELAY)
                    continue

                # Handle device unauthorized
                if "unauthorized" in stderr.lower() or "unauthorized" in stdout.lower():
                    logger.warning("Device unauthorized — user must accept RSA key dialog")
                    return ADBResult(
                        success=False,
                        stdout=stdout,
                        stderr="Device unauthorized. Accept the RSA key dialog on the device.",
                        returncode=proc.returncode,
                        command=cmd_str,
                    )

                logger.warning(
                    f"ADB command failed (attempt {attempt + 1}): {cmd_str}\n"
                    f"  stdout: {stdout}\n  stderr: {stderr}"
                )

                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY * (attempt + 1))

            except subprocess.TimeoutExpired:
                logger.error(f"ADB command timed out after {timeout}s: {cmd_str}")
                return ADBResult(
                    success=False,
                    stderr=f"Command timed out after {timeout} seconds",
                    command=cmd_str,
                )
            except FileNotFoundError:
                logger.critical(f"ADB binary not found at: {self._adb_path}")
                return ADBResult(
                    success=False,
                    stderr=f"ADB binary not found: {self._adb_path}",
                    command=cmd_str,
                )

        return ADBResult(
            success=False,
            stderr=f"Command failed after {self.MAX_RETRIES} attempts",
            command=cmd_str,
        )
