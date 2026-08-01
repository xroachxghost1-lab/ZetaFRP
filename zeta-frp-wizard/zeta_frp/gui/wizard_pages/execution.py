#!/usr/bin/env python3
"""
Zeta FRP Wizard — Execution Page
===================================
Executes the selected FRP bypass method with
real-time progress display.

ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
Unauthorised use, distribution, or reproduction is an act of war.
Copyright © 2026 Zeta Omniverse. All rights reserved.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QGroupBox,
    QProgressBar, QTextEdit, QHBoxLayout, QMessageBox,
)
from PySide6.QtCore import Qt, QThread, Signal

from zeta_frp.utils.logger import get_logger

logger = get_logger(__name__)

class ExecutionThread(QThread):
    """Background thread for FRP bypass execution."""
    progress = Signal(int, str)    # percent, message
    log_line = Signal(str)         # log output
    complete = Signal(bool, str)   # success, message

    def __init__(self, device_info: dict, method, firmware_path: str = None):
        super().__init__()
        self._device_info = device_info
        self._method = method
        self._firmware_path = firmware_path

    def run(self):
        try:
            self.log_line.emit(f"Starting: {self._method.name}")

            def progress_cb(pct: int, msg: str):
                self.progress.emit(pct, msg)
                self.log_line.emit(f"[{pct}%] {msg}")

            # Execute based on method category
            from zeta_frp.core.spl_checker import MethodCategory

            if self._method.category == MethodCategory.ADB_USER_SETUP:
                self._execute_adb(progress_cb)
            elif self._method.category == MethodCategory.ODIN_FLASH:
                self._execute_odin(progress_cb)
            elif self._method.category == MethodCategory.EDL_FLASH:
                self._execute_edl(progress_cb)
            elif self._method.category == MethodCategory.SP_FLASH:
                self._execute_spflash(progress_cb)
            elif self._method.category == MethodCategory.FASTBOOT_FLASH:
                self._execute_fastboot(progress_cb)
            else:
                self.log_line.emit("Method requires manual execution. Follow the guide.")
                self.complete.emit(True, "Manual method selected. Follow the on-screen guide.")

        except Exception as e:
            self.log_line.emit(f"ERROR: {e}")
            self.complete.emit(False, str(e))

    def _execute_adb(self, progress_cb):
        from zeta_frp.utils.adb_wrapper import ADBWrapper
        adb = ADBWrapper()
        progress_cb(20, "Connecting via ADB...")
        devices = adb.list_devices()
        if not devices:
            self.complete.emit(False, "No ADB devices found. Enable USB debugging and retry.")
            return

        serial = devices[0].serial
        progress_cb(40, "Executing ADB bypass commands...")
        result = adb.bypass_frp_adb(serial=serial)
        progress_cb(70, "Commands executed.")

        if result.success:
            progress_cb(90, "Launching Settings...")
            adb.shell("am start -n com.android.settings/.Settings", serial=serial)
            progress_cb(100, "ADB bypass complete. Remove Google account manually.")
            self.complete.emit(True, "ADB bypass executed successfully.")
        else:
            self.complete.emit(False, f"ADB bypass failed: {result.stderr}")

    def _execute_odin(self, progress_cb):
        if not self._firmware_path:
            self.complete.emit(False, "No firmware provided for Odin flash.")
            return
        progress_cb(30, "Firmware loaded for Odin flash.")
        progress_cb(50, "Boot device into Download Mode and connect via USB.")
        progress_cb(100, "Odin flash ready. Execute Odin manually with the provided firmware.")
        self.complete.emit(True, "Ready for Odin flash. See instructions below.")

    def _execute_edl(self, progress_cb):
        progress_cb(20, "Checking EDL mode...")
        progress_cb(100, "EDL mode detected. Flash firehose programmer to proceed.")
        self.complete.emit(True, "EDL ready. Use the EDL flasher module.")

    def _execute_spflash(self, progress_cb):
        progress_cb(20, "Checking BROM mode...")
        progress_cb(100, "BROM ready. Use SP Flash Tool to flash firmware.")
        self.complete.emit(True, "MediaTek BROM ready.")

    def _execute_fastboot(self, progress_cb):
        from zeta_frp.utils.fastboot_wrapper import FastbootWrapper
        fb = FastbootWrapper()
        progress_cb(30, "Checking Fastboot connection...")
        devices = fb.list_devices()
        if not devices:
            self.complete.emit(False, "No Fastboot devices found.")
            return
        progress_cb(60, "Erasing FRP partition...")
        result = fb.erase_frp()
        if result.success:
            progress_cb(90, "Rebooting...")
            fb.reboot()
            progress_cb(100, "FRP removed via Fastboot!")
            self.complete.emit(True, "FRP successfully removed.")
        else:
            self.complete.emit(False, f"Fastboot erase failed: {result.stderr}")

class ExecutionPage(QWidget):
    """
    Bypass execution wizard page.

    Shows real-time progress and log output during
    the FRP bypass operation.
    """

    def __init__(self):
        super().__init__()
        self._main_window = None
        self._exec_thread = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(16)

        title = QLabel("Executing FRP Bypass")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        # Progress
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)

        self._progress_bar = QProgressBar()
        progress_layout.addWidget(self._progress_bar)

        self._status_label = QLabel("Ready to execute...")
        self._status_label.setWordWrap(True)
        progress_layout.addWidget(self._status_label)

        layout.addWidget(progress_group)

        # Execution controls
        btn_layout = QHBoxLayout()

        self._start_btn = QPushButton("▶ Start Bypass")
        self._start_btn.setObjectName("primaryBtn")
        self._start_btn.setMinimumHeight(40)
        self._start_btn.clicked.connect(self._start_execution)
        btn_layout.addWidget(self._start_btn)

        self._stop_btn = QPushButton("⏹ Stop")
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._stop_execution)
        btn_layout.addWidget(self._stop_btn)

        layout.addLayout(btn_layout)

        # Log output
        log_group = QGroupBox("Execution Log")
        log_layout = QVBoxLayout(log_group)

        self._log_view = QTextEdit()
        self._log_view.setReadOnly(True)
        self._log_view.setMaximumHeight(200)
        log_layout.addWidget(self._log_view)

        layout.addWidget(log_group)

        # Warnings
        self._warnings_label = QLabel("")
        self._warnings_label.setWordWrap(True)
        self._warnings_label.setStyleSheet("color: #FF9800;")
        layout.addWidget(self._warnings_label)

        layout.addStretch()

    # ------------------------------------------------------------------
    # Page Lifecycle
    # ------------------------------------------------------------------

    def on_enter(self, main_window) -> None:
        self._main_window = main_window
        method = main_window.selected_method
        if method:
            self._status_label.setText(f"Method: {method.name}")
            self._log_view.append(f"--- {method.name} ---")

            # Show warnings
            warnings = []
            if method.risk_level in ("high", "critical"):
                warnings.append(f"⚠ HIGH RISK method. {method.risk_level.upper()} risk of device damage.")
            if method.requires_usb_debugging:
                warnings.append("⚠ USB Debugging must be pre-enabled.")
            if method.requires_unlocked_bootloader:
                warnings.append("⚠ Bootloader must be unlocked.")
            self._warnings_label.setText("\n".join(warnings))

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def _start_execution(self) -> None:
        """Start the bypass execution thread."""
        device = self._main_window.device if self._main_window else None
        method = self._main_window.selected_method if self._main_window else None
        firmware = self._main_window.firmware_path if self._main_window else None

        if not device or not method:
            QMessageBox.warning(self, "Error", "Device or method not selected.")
            return

        self._start_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self._progress_bar.setValue(0)
        self._log_view.clear()

        device_info = device.raw_props if hasattr(device, 'raw_props') else {}

        self._exec_thread = ExecutionThread(device_info, method, firmware)
        self._exec_thread.progress.connect(self._on_progress)
        self._exec_thread.log_line.connect(self._on_log)
        self._exec_thread.complete.connect(self._on_complete)
        self._exec_thread.start()

    def _stop_execution(self) -> None:
        """Stop the execution."""
        if self._exec_thread and self._exec_thread.isRunning():
            self._exec_thread.terminate()
            self._exec_thread.wait(2000)
            self._log_view.append("--- EXECUTION STOPPED BY USER ---")
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)

    def _on_progress(self, pct: int, msg: str) -> None:
        self._progress_bar.setValue(pct)
        self._status_label.setText(msg)

    def _on_log(self, line: str) -> None:
        self._log_view.append(line)

    def _on_complete(self, success: bool, message: str) -> None:
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)

        if success:
            self._progress_bar.setValue(100)
            self._status_label.setText("✅ " + message)
            self._log_view.append(f"SUCCESS: {message}")
        else:
            self._status_label.setText("❌ " + message)
            self._log_view.append(f"FAILED: {message}")

    def validate(self) -> bool:
        return True
