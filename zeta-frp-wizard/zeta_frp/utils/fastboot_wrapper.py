#!/usr/bin/env python3
"""
Zeta FRP Wizard — Fastboot Wrapper (Bare-Level Implementation)
===============================================================
Pure subprocess-based Fastboot client for bootloader-level
device operations. Used for unlocking, flashing, and rebooting
devices in Fastboot mode.

ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
Unauthorised use, distribution, or reproduction is an act of war.
Copyright © 2026 Zeta Omniverse. All rights reserved.
"""

import subprocess
import os
import time
import re
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass

from zeta_frp.utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class FastbootDevice:
    """Represents a device in Fastboot mode."""
    serial: str
    product: str = ""
    variant: str = ""
    secure: bool = True
    unlocked: bool = False

@dataclass
class FastbootResult:
    """Result of a Fastboot command execution."""
    success: bool
    stdout: str = ""
    stderr: str = ""
    returncode: int = -1
    command: str = ""

class FastbootWrapper:
    """
    Bare-level Fastboot client.

    Usage:
        fb = FastbootWrapper()
        devices = fb.list_devices()
        fb.unlock_bootloader()
        fb.flash_partition("boot", "boot.img")
        fb.reboot()
    """

    DEFAULT_TIMEOUT = 30
    FLASH_TIMEOUT = 300  # 5 minutes for large partitions

    def __init__(self, fastboot_path: Optional[str] = None):
        self._fb_path = fastboot_path or self._find_fastboot()

    def _find_fastboot(self) -> str:
        """Locate the Fastboot binary."""
        # Bundled
        base = Path(__file__).parent.parent.parent / "resources" / "adb"
        candidates = []
        if os.name == "nt":
            candidates = [base / "fastboot.exe"]
        else:
            candidates = [base / "fastboot"]

        for c in candidates:
            if c.exists():
                return str(c)

        # Environment
        env_path = os.environ.get("FASTBOOT_PATH")
        if env_path and Path(env_path).exists():
            return env_path

        # System PATH
        import shutil
        fb = shutil.which("fastboot")
        if fb:
            return fb

        return "fastboot"

    # ------------------------------------------------------------------
    # Device Management
    # ------------------------------------------------------------------

    def list_devices(self) -> List[FastbootDevice]:
        """List devices in Fastboot mode."""
        result = self._run_fb(["devices", "-l"], timeout=10)
        devices = []
        if result.success:
            for line in result.stdout.strip().split("\n"):
                if not line.strip() or "fastboot" not in line:
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    dev = FastbootDevice(serial=parts[0])
                    for part in parts[1:]:
                        if part.startswith("product:"):
                            dev.product = part.split(":", 1)[1]
                        elif part.startswith("variant:"):
                            dev.variant = part.split(":", 1)[1]
                    devices.append(dev)
        return devices

    def get_device(self, serial: Optional[str] = None) -> Optional[FastbootDevice]:
        """Get a specific Fastboot device."""
        devices = self.list_devices()
        if not devices:
            return None
        if serial:
            for d in devices:
                if d.serial == serial:
                    return d
            return None
        return devices[0]

    # ------------------------------------------------------------------
    # Device Info
    # ------------------------------------------------------------------

    def get_var(self, var: str, serial: Optional[str] = None) -> str:
        """Get a bootloader variable."""
        cmd = self._build_cmd(["getvar", var], serial)
        result = self._run_fb(cmd)
        if result.success:
            match = re.search(rf"{var}:\s*(.+)", result.stdout)
            if match:
                return match.group(1).strip()
        return ""

    def get_all_vars(self, serial: Optional[str] = None) -> Dict[str, str]:
        """Get all bootloader variables."""
        result = self._run_fb(self._build_cmd(["getvar", "all"], serial), timeout=30)
        vars_dict = {}
        if result.success:
            for line in result.stdout.split("\n"):
                match = re.match(r"\(bootloader\)\s*(\S+):\s*(.+)", line)
                if match:
                    vars_dict[match.group(1)] = match.group(2).strip()
        return vars_dict

    def get_unlock_status(self, serial: Optional[str] = None) -> bool:
        """Check if bootloader is unlocked."""
        status = self.get_var("unlocked", serial)
        return status.lower() == "yes"

    # ------------------------------------------------------------------
    # Flashing Operations
    # ------------------------------------------------------------------

    def flash_partition(self, partition: str, image_path: str,
                        serial: Optional[str] = None) -> FastbootResult:
        """
        Flash an image to a partition.

        Args:
            partition: Partition name (boot, recovery, system, vendor, etc.)
            image_path: Path to the image file on the host.
            serial: Target device serial.
        """
        if not Path(image_path).exists():
            return FastbootResult(
                success=False,
                stderr=f"Image file not found: {image_path}",
                command=f"flash {partition} {image_path}",
            )
        cmd = self._build_cmd(["flash", partition, image_path], serial)
        logger.info(f"Flashing {partition} with {image_path}...")
        return self._run_fb(cmd, timeout=self.FLASH_TIMEOUT)

    def flash_all(self, serial: Optional[str] = None) -> FastbootResult:
        """Execute 'flashall' — flash all partitions from current directory."""
        return self._run_fb(
            self._build_cmd(["flashall"], serial), timeout=self.FLASH_TIMEOUT
        )

    def erase_partition(self, partition: str,
                        serial: Optional[str] = None) -> FastbootResult:
        """Erase a partition."""
        cmd = self._build_cmd(["erase", partition], serial)
        logger.warning(f"Erasing partition: {partition}")
        return self._run_fb(cmd, timeout=60)

    def format_partition(self, partition: str, fs_type: str = "ext4",
                         serial: Optional[str] = None) -> FastbootResult:
        """Format a partition with the specified filesystem."""
        cmd = self._build_cmd(["format", fs_type, partition], serial)
        logger.info(f"Formatting {partition} as {fs_type}")
        return self._run_fb(cmd, timeout=120)

    # ------------------------------------------------------------------
    # Boot & Reboot
    # ------------------------------------------------------------------

    def boot_image(self, image_path: str,
                   serial: Optional[str] = None) -> FastbootResult:
        """Boot a kernel image without flashing it."""
        cmd = self._build_cmd(["boot", image_path], serial)
        return self._run_fb(cmd, timeout=60)

    def reboot(self, target: str = "",
               serial: Optional[str] = None) -> FastbootResult:
        """Reboot the device. Target: '' (system), 'bootloader', 'recovery'."""
        cmd = self._build_cmd(["reboot"], serial)
        if target:
            cmd.append(target)
        return self._run_fb(cmd, timeout=30)

    def reboot_bootloader(self, serial: Optional[str] = None) -> FastbootResult:
        """Reboot back into bootloader."""
        return self.reboot("bootloader", serial)

    def continue_boot(self, serial: Optional[str] = None) -> FastbootResult:
        """Continue booting (exit fastboot without reboot)."""
        return self._run_fb(self._build_cmd(["continue"], serial), timeout=10)

    # ------------------------------------------------------------------
    # Bootloader Operations
    # ------------------------------------------------------------------

    def oem_unlock(self, serial: Optional[str] = None) -> FastbootResult:
        """
        Unlock the bootloader. WARNING: This wipes user data on most devices.
        """
        logger.warning("UNLOCKING BOOTLOADER — THIS WILL WIPE USER DATA")
        return self._run_fb(self._build_cmd(["oem", "unlock"], serial), timeout=30)

    def oem_lock(self, serial: Optional[str] = None) -> FastbootResult:
        """Re-lock the bootloader."""
        return self._run_fb(self._build_cmd(["oem", "lock"], serial), timeout=30)

    def flashing_unlock(self, serial: Optional[str] = None) -> FastbootResult:
        """Unlock flashing (some devices use this instead of oem unlock)."""
        return self._run_fb(
            self._build_cmd(["flashing", "unlock"], serial), timeout=30
        )

    def flashing_lock(self, serial: Optional[str] = None) -> FastbootResult:
        """Lock flashing."""
        return self._run_fb(
            self._build_cmd(["flashing", "lock"], serial), timeout=30
        )

    # ------------------------------------------------------------------
    # OEM-Specific
    # ------------------------------------------------------------------

    def oem_device_info(self, serial: Optional[str] = None) -> FastbootResult:
        """Get OEM device information."""
        return self._run_fb(
            self._build_cmd(["oem", "device-info"], serial), timeout=10
        )

    def oem_get_imei(self, serial: Optional[str] = None) -> str:
        """Attempt to get IMEI from fastboot (works on some Xiaomi devices)."""
        result = self._run_fb(
            self._build_cmd(["oem", "get_imei"], serial), timeout=10
        )
        if result.success:
            for line in result.stdout.split("\n"):
                if "IMEI" in line:
                    return line.split(":")[-1].strip()
        return ""

    # ------------------------------------------------------------------
    # FRP-Specific
    # ------------------------------------------------------------------

    def erase_frp(self, serial: Optional[str] = None) -> FastbootResult:
        """
        Erase the FRP partition. This removes Factory Reset Protection
        on devices that store FRP state in a dedicated partition.
        NOTE: Not all devices have a named 'frp' partition.
        """
        logger.warning("Erasing FRP partition...")
        return self.erase_partition("frp", serial)

    def erase_persist(self, serial: Optional[str] = None) -> FastbootResult:
        """
        Erase the persist partition. On some devices (Xiaomi, Motorola),
        FRP state is stored here. WARNING: May cause sensor calibration loss.
        """
        logger.warning("Erasing persist partition — may affect sensors!")
        return self.erase_partition("persist", serial)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _build_cmd(self, base_cmd: List[str],
                   serial: Optional[str] = None) -> List[str]:
        """Build full command with optional device serial."""
        cmd = [self._fb_path]
        if serial:
            cmd.extend(["-s", serial])
        cmd.extend(base_cmd)
        return cmd

    def _run_fb(self, cmd: List[str],
                timeout: int = DEFAULT_TIMEOUT) -> FastbootResult:
        """Execute a Fastboot command."""
        cmd_str = " ".join(cmd)
        logger.debug(f"FASTBOOT: {cmd_str}")

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            stdout = proc.stdout.strip()
            stderr = proc.stderr.strip()

            # Fastboot returns non-zero for some info commands even on success
            if "OKAY" in stdout or "finished" in stdout.lower():
                return FastbootResult(
                    success=True,
                    stdout=stdout,
                    stderr=stderr,
                    returncode=proc.returncode,
                    command=cmd_str,
                )

            if proc.returncode != 0 and "FAILED" in stdout:
                logger.error(f"Fastboot FAILED: {cmd_str}\n  {stdout}")
                return FastbootResult(
                    success=False,
                    stdout=stdout,
                    stderr=stderr,
                    returncode=proc.returncode,
                    command=cmd_str,
                )

            # Treat as success if we got output and no explicit FAILED
            return FastbootResult(
                success="FAILED" not in stdout,
                stdout=stdout,
                stderr=stderr,
                returncode=proc.returncode,
                command=cmd_str,
            )

        except subprocess.TimeoutExpired:
            logger.error(f"Fastboot timed out: {cmd_str}")
            return FastbootResult(
                success=False,
                stderr=f"Command timed out after {timeout}s",
                command=cmd_str,
            )
        except FileNotFoundError:
            logger.critical(f"Fastboot binary not found: {self._fb_path}")
            return FastbootResult(
                success=False,
                stderr=f"Fastboot binary not found: {self._fb_path}",
                command=cmd_str,
            )
