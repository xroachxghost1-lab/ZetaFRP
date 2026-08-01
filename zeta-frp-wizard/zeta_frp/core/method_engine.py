#!/usr/bin/env python3
"""
Zeta FRP Wizard — Method Selection Engine
==========================================
Strategy pattern engine that selects and orchestrates
the optimal FRP bypass method based on device state.

ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
Unauthorised use, distribution, or reproduction is an act of war.
Copyright © 2026 Zeta Omniverse. All rights reserved.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Callable
from enum import Enum, auto

from zeta_frp.utils.logger import get_logger
from zeta_frp.core.spl_checker import SPLChecker, MethodAvailability, MethodCategory
from zeta_frp.core.device_detector import DetectedDevice, DeviceMode

logger = get_logger(__name__)

class ExecutionPhase(Enum):
    """Phases of FRP bypass execution."""
    PRE_CHECK = auto()
    PREPARE = auto()
    FLASH = auto()
    BYPASS = auto()
    VERIFY = auto()
    CLEANUP = auto()

@dataclass
class ExecutionStep:
    """A single step in the bypass execution plan."""
    phase: ExecutionPhase
    description: str
    command: Optional[str] = None
    timeout: int = 30
    critical: bool = True  # If True, failure aborts the entire plan

@dataclass
class ExecutionPlan:
    """Complete execution plan for FRP bypass."""
    method: MethodAvailability
    device: DetectedDevice
    steps: List[ExecutionStep] = field(default_factory=list)
    estimated_time: int = 60  # seconds
    warnings: List[str] = field(default_factory=list)

    def add_step(self, phase: ExecutionPhase, description: str,
                 command: Optional[str] = None, timeout: int = 30,
                 critical: bool = True) -> None:
        self.steps.append(ExecutionStep(
            phase=phase, description=description,
            command=command, timeout=timeout, critical=critical,
        ))

    def add_warning(self, warning: str) -> None:
        self.warnings.append(warning)

@dataclass
class ExecutionResult:
    """Result of executing a bypass method."""
    success: bool
    method_name: str
    steps_completed: int
    steps_total: int
    error: str = ""
    log: List[str] = field(default_factory=list)

class MethodEngine:
    """
    Strategy engine for FRP bypass method selection and execution.

    Usage:
        engine = MethodEngine()
        device = detector.scan()[0]
        plan = engine.create_plan(device)
        result = engine.execute_plan(plan)
    """

    def __init__(self):
        self._spl_checker = SPLChecker()

    # ------------------------------------------------------------------
    # Plan Creation
    # ------------------------------------------------------------------

    def create_plan(self, device: DetectedDevice,
                    force_method: Optional[MethodCategory] = None) -> ExecutionPlan:
        """
        Create an execution plan for bypassing FRP on the given device.

        Args:
            device: The detected device to bypass.
            force_method: If provided, use this method regardless of SPL checks.

        Returns:
            An ExecutionPlan ready for execution.

        Raises:
            ValueError: If no method is available for this device.
        """
        if force_method:
            method = self._find_method_by_category(force_method)
            if method is None:
                raise ValueError(f"Method {force_method} not found in database")
        else:
            # Parse SPL date
            spl_date = None
            if device.security_patch:
                from datetime import datetime
                try:
                    spl_date = datetime.strptime(device.security_patch, "%Y-%m-%d")
                except ValueError:
                    pass

            usb_debugging = device.mode == DeviceMode.ADB
            bootloader_unlocked = False  # We can't know until we check

            method = self._spl_checker.get_recommended_method(
                manufacturer=device.manufacturer,
                android_sdk=device.sdk_level,
                spl_date=spl_date,
                usb_debugging=usb_debugging,
                bootloader_unlocked=bootloader_unlocked,
            )

        if method is None:
            raise ValueError(
                f"No FRP bypass method available for {device.display_name}. "
                f"Device may require manual intervention or is too new for current exploits."
            )

        # Build the plan based on method category
        plan = ExecutionPlan(method=method, device=device)

        if method.category == MethodCategory.ADB_USER_SETUP:
            self._build_adb_plan(plan)
        elif method.category == MethodCategory.ODIN_FLASH:
            self._build_odin_plan(plan)
        elif method.category == MethodCategory.EDL_FLASH:
            self._build_edl_plan(plan)
        elif method.category == MethodCategory.SP_FLASH:
            self._build_sp_flash_plan(plan)
        elif method.category == MethodCategory.FASTBOOT_FLASH:
            self._build_fastboot_plan(plan)
        elif method.category in (MethodCategory.INTERACTIVE_TALKBACK,
                                  MethodCategory.INTERACTIVE_EMERGENCY,
                                  MethodCategory.INTERACTIVE_KEYBOARD):
            self._build_interactive_plan(plan)
        else:
            self._build_generic_plan(plan)

        logger.info(
            f"Plan created for {device.display_name}: "
            f"{method.name} ({len(plan.steps)} steps, ~{plan.estimated_time}s)"
        )
        return plan

    # ------------------------------------------------------------------
    # Plan Builders (per method category)
    # ------------------------------------------------------------------

    def _build_adb_plan(self, plan: ExecutionPlan) -> None:
        plan.estimated_time = 30
        plan.add_step(ExecutionPhase.PRE_CHECK, "Verify ADB connection to device")
        plan.add_step(ExecutionPhase.PRE_CHECK, "Check if USB debugging is authorized")
        plan.add_step(
            ExecutionPhase.BYPASS,
            "Set user_setup_complete=1 in secure settings",
            command="content insert --uri content://settings/secure --bind name:s:user_setup_complete --bind value:i:1",
            timeout=10,
        )
        plan.add_step(
            ExecutionPhase.BYPASS,
            "Set device_provisioned=1 in global settings",
            command="content insert --uri content://settings/global --bind name:s:device_provisioned --bind value:i:1",
            timeout=10,
        )
        plan.add_step(
            ExecutionPhase.BYPASS,
            "Launch Android Settings",
            command="am start -n com.android.settings/.Settings",
            timeout=10,
        )
        plan.add_step(
            ExecutionPhase.VERIFY,
            "Manually navigate to Accounts and remove Google account",
            timeout=60,
            critical=False,
        )
        plan.add_step(ExecutionPhase.CLEANUP, "Reboot device to apply changes")
        plan.add_warning(
            "USB debugging must have been enabled BEFORE the factory reset. "
            "If not, this method will fail and you must use a flashing-based method."
        )

    def _build_odin_plan(self, plan: ExecutionPlan) -> None:
        plan.estimated_time = 600  # 10 minutes including firmware download
        plan.add_step(
            ExecutionPhase.PRE_CHECK,
            "Verify device model and binary version for firmware compatibility"
        )
        plan.add_step(
            ExecutionPhase.PREPARE,
            "Download combination firmware for this model (or use provided firmware)",
            timeout=300,
        )
        plan.add_step(
            ExecutionPhase.PREPARE,
            "Boot device into Download Mode (Volume Down + Home + Power)",
            timeout=30,
        )
        plan.add_step(
            ExecutionPhase.FLASH,
            "Flash combination firmware via Odin",
            timeout=180,
        )
        plan.add_step(
            ExecutionPhase.BYPASS,
            "Wait for device to boot to factory binary",
            timeout=120,
        )
        plan.add_step(
            ExecutionPhase.BYPASS,
            "Execute ADB FRP removal commands on combination firmware",
            timeout=30,
        )
        plan.add_step(
            ExecutionPhase.CLEANUP,
            "Flash stock firmware back to device",
            timeout=180,
            critical=False,
        )
        plan.add_warning(
            "Flashing combination firmware will wipe all user data. "
            "Ensure the correct firmware is used — wrong firmware can brick the device."
        )
        plan.add_warning(
            "Samsung Kies servers now require IMEI validation for firmware downloads. "
            "Have your device IMEI ready."
        )

    def _build_edl_plan(self, plan: ExecutionPlan) -> None:
        plan.estimated_time = 480
        plan.add_step(
            ExecutionPhase.PREPARE,
            "Force device into EDL (9008) mode — may require test point or button combination",
            timeout=60,
        )
        plan.add_step(
            ExecutionPhase.PREPARE,
            "Load Qualcomm Sahara/Firehose programmer for this device",
            timeout=30,
        )
        plan.add_step(
            ExecutionPhase.FLASH,
            "Flash patched boot image with ADB enabled",
            timeout=120,
        )
        plan.add_step(
            ExecutionPhase.BYPASS,
            "Reboot and execute ADB FRP removal",
            timeout=60,
        )
        plan.add_step(
            ExecutionPhase.CLEANUP,
            "Flash stock boot image back",
            timeout=120,
            critical=False,
        )
        plan.add_warning(
            "EDL flashing is HIGH RISK. Incorrect firehose programmer can hard-brick "
            "the device. Verify the programmer file matches your exact model."
        )

    def _build_sp_flash_plan(self, plan: ExecutionPlan) -> None:
        plan.estimated_time = 480
        plan.add_step(
            ExecutionPhase.PREPARE,
            "Install MediaTek VCOM drivers",
            timeout=60,
        )
        plan.add_step(
            ExecutionPhase.PREPARE,
            "Force device into BROM mode (test point or volume keys + USB)",
            timeout=60,
        )
        plan.add_step(
            ExecutionPhase.PREPARE,
            "Load scatter file for this device",
            timeout=30,
        )
        plan.add_step(
            ExecutionPhase.FLASH,
            "Flash firmware via SP Flash Tool with FRP partition erase",
            timeout=180,
        )
        plan.add_step(
            ExecutionPhase.VERIFY,
            "Reboot device and verify FRP is removed",
            timeout=60,
        )
        plan.add_warning(
            "MediaTek flashing can cause IMEI loss if NVRAM is overwritten. "
            "Backup NVRAM before flashing if possible."
        )

    def _build_fastboot_plan(self, plan: ExecutionPlan) -> None:
        plan.estimated_time = 120
        plan.add_step(
            ExecutionPhase.PRE_CHECK,
            "Verify bootloader is unlocked (required for Fastboot flash)",
        )
        plan.add_step(
            ExecutionPhase.PREPARE,
            "Boot device into Fastboot mode",
            timeout=30,
        )
        plan.add_step(
            ExecutionPhase.FLASH,
            "Erase FRP partition",
            command="fastboot erase frp",
            timeout=30,
        )
        plan.add_step(
            ExecutionPhase.FLASH,
            "Erase persist partition (fallback)",
            command="fastboot erase persist",
            timeout=30,
            critical=False,
        )
        plan.add_step(
            ExecutionPhase.CLEANUP,
            "Reboot device",
            command="fastboot reboot",
            timeout=30,
        )
        plan.add_warning(
            "Erasing persist partition may cause sensor calibration loss "
            "(fingerprint, proximity, etc.). Use only if FRP partition erase fails."
        )

    def _build_interactive_plan(self, plan: ExecutionPlan) -> None:
        plan.estimated_time = 300
        method_name = plan.method.name
        plan.add_step(
            ExecutionPhase.PRE_CHECK,
            f"Confirm device is at the Google account verification screen"
        )
        plan.add_step(
            ExecutionPhase.PREPARE,
            "Connect to WiFi (required for some interactive methods)",
            timeout=60,
        )
        plan.add_step(
            ExecutionPhase.BYPASS,
            f"Follow on-screen guide for: {method_name}",
            timeout=180,
        )
        plan.add_step(
            ExecutionPhase.BYPASS,
            "Navigate to Settings > Accounts > Remove Google account",
            timeout=60,
        )
        plan.add_step(
            ExecutionPhase.VERIFY,
            "Factory reset device again to complete bypass",
            timeout=30,
        )
        plan.add_warning(
            f"Interactive methods like {method_name} are patched on newer "
            "Security Patch Levels. This method may not work on your device."
        )

    def _build_generic_plan(self, plan: ExecutionPlan) -> None:
        plan.estimated_time = 60
        plan.add_step(ExecutionPhase.PRE_CHECK, "Verify device connection")
        plan.add_step(
            ExecutionPhase.BYPASS,
            f"Execute: {plan.method.name}",
            timeout=60,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _find_method_by_category(self, category: MethodCategory) -> Optional[MethodAvailability]:
        """Find a method in the database by its category."""
        for method in self._spl_checker.METHOD_DB:
            if method.category == category:
                return method
        return None

    def get_all_methods_for_device(self, device: DetectedDevice) -> List[MethodAvailability]:
        """Get all potentially applicable methods for a device (for UI display)."""
        from datetime import datetime
        spl_date = None
        if device.security_patch:
            try:
                spl_date = datetime.strptime(device.security_patch, "%Y-%m-%d")
            except ValueError:
                pass

        results = self._spl_checker.get_available_methods(
            manufacturer=device.manufacturer,
            android_sdk=device.sdk_level,
            spl_date=spl_date,
            usb_debugging=(device.mode == DeviceMode.ADB),
            bootloader_unlocked=False,
        )
        return [m for m, _ in results]
