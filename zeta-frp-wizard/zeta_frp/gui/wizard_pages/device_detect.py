#!/usr/bin/env python3
"""
Zeta FRP Wizard — Device Detection Page
==========================================
Scans for connected Android devices and displays
detailed device information.

ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
Unauthorised use, distribution, or reproduction is an act of war.
Copyright © 2026 Zeta Omniverse. All rights reserved.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QGroupBox,
    QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QMessageBox,
)
from PySide6.QtCore import Qt, QThread, Signal

from zeta_frp.core.device_detector import DeviceDetector, DetectedDevice
from zeta_frp.utils.logger import get_logger

logger = get_logger(__name__)

class ScanThread(QThread):
    """Background thread for device scanning."""
    devices_found = Signal(list)
    scan_complete = Signal()
    error = Signal(str)

    def run(self):
        try:
            detector = DeviceDetector()
            devices = detector.scan()
            self.devices_found.emit(devices)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.scan_complete.emit()

class DeviceDetectPage(QWidget):
    """
    Device detection wizard page.

    Scans for:
    - ADB devices (normal, recovery, sideload)
    - Fastboot devices
    - Qualcomm EDL (9008)
    - MediaTek BROM
    """

    def __init__(self):
        super().__init__()
        self._devices = []
        self._scan_thread = None
        self._main_window = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(16)

        # Title
        title = QLabel("Device Detection")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        # Instructions
        instructions = QLabel(
            "Connect your Android device via USB and click 'Scan for Devices'.\n"
            "The wizard will automatically detect your device model and connection mode."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Scan button + progress
        scan_layout = QHBoxLayout()
        self._scan_btn = QPushButton("🔍 Scan for Devices")
        self._scan_btn.setObjectName("primaryBtn")
        self._scan_btn.clicked.connect(self._scan_devices)
        self._scan_btn.setMinimumHeight(40)

        self._scan_progress = QProgressBar()
        self._scan_progress.setRange(0, 0)  # Indeterminate
        self._scan_progress.setVisible(False)

        scan_layout.addWidget(self._scan_btn)
        scan_layout.addWidget(self._scan_progress)
        layout.addLayout(scan_layout)

        # Device table
        table_group = QGroupBox("Detected Devices")
        table_layout = QVBoxLayout(table_group)

        self._device_table = QTableWidget(0, 5)
        self._device_table.setHorizontalHeaderLabels([
            "Serial", "Manufacturer", "Model", "Mode", "Android Version"
        ])
        self._device_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._device_table.setSelectionBehavior(QTableWidget.SelectRows)
        self._device_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._device_table.itemSelectionChanged.connect(self._on_selection_changed)
        table_layout.addWidget(self._device_table)

        layout.addWidget(table_group)

        # Device details
        self._details_group = QGroupBox("Device Details")
        self._details_group.setVisible(False)
        details_layout = QVBoxLayout(self._details_group)
        self._details_label = QLabel("")
        self._details_label.setWordWrap(True)
        details_layout.addWidget(self._details_label)
        layout.addWidget(self._details_group)

        # Manual mode help
        help_label = QLabel(
            "<b>Device not detected?</b><br>"
            "• Ensure USB debugging is enabled (if device is booted)<br>"
            "• Try a different USB cable or port<br>"
            "• For EDL/BROM modes: power off device and use specific key combinations<br>"
            "• Install drivers using the 'Install Drivers' button on the Welcome page"
        )
        help_label.setWordWrap(True)
        help_label.setObjectName("helpText")
        layout.addWidget(help_label)

        layout.addStretch()

    # ------------------------------------------------------------------
    # Scan Logic
    # ------------------------------------------------------------------

    def _scan_devices(self) -> None:
        """Initiate device scan in background thread."""
        self._scan_btn.setEnabled(False)
        self._scan_progress.setVisible(True)
        self._device_table.setRowCount(0)
        self._devices = []

        self._scan_thread = ScanThread()
        self._scan_thread.devices_found.connect(self._on_devices_found)
        self._scan_thread.scan_complete.connect(self._on_scan_complete)
        self._scan_thread.error.connect(self._on_scan_error)
        self._scan_thread.start()

    def _on_devices_found(self, devices: list) -> None:
        """Populate the device table with scan results."""
        self._devices = devices
        self._device_table.setRowCount(len(devices))

        for i, device in enumerate(devices):
            self._device_table.setItem(i, 0, QTableWidgetItem(device.serial[:16]))
            self._device_table.setItem(i, 1, QTableWidgetItem(device.manufacturer))
            self._device_table.setItem(i, 2, QTableWidgetItem(device.model))
            self._device_table.setItem(i, 3, QTableWidgetItem(device.mode.name))
            self._device_table.setItem(i, 4, QTableWidgetItem(
                device.android_version or "Unknown"
            ))

    def _on_scan_complete(self) -> None:
        """Scan finished."""
        self._scan_btn.setEnabled(True)
        self._scan_progress.setVisible(False)

        if not self._devices:
            self._details_group.setVisible(False)
            logger.info("No devices found")

    def _on_scan_error(self, error: str) -> None:
        """Handle scan errors."""
        self._scan_btn.setEnabled(True)
        self._scan_progress.setVisible(False)
        QMessageBox.warning(self, "Scan Error", f"Device scan failed:\n{error}")

    def _on_selection_changed(self) -> None:
        """Update device details when a row is selected."""
        row = self._device_table.currentRow()
        if 0 <= row < len(self._devices):
            device = self._devices[row]
            details = (
                f"<b>Serial:</b> {device.serial}<br>"
                f"<b>Manufacturer:</b> {device.manufacturer}<br>"
                f"<b>Model:</b> {device.model}<br>"
                f"<b>Mode:</b> {device.mode.name}<br>"
                f"<b>Android:</b> {device.android_version or 'Unknown'}<br>"
                f"<b>Security Patch:</b> {device.security_patch or 'Unknown'}<br>"
                f"<b>SDK Level:</b> {device.sdk_level or 'Unknown'}<br>"
                f"<b>SoC:</b> {device.soc_manufacturer or 'Unknown'}<br>"
                f"<b>Product:</b> {device.product or 'Unknown'}"
            )
            self._details_label.setText(details)
            self._details_group.setVisible(True)

            # Notify main window
            if self._main_window:
                self._main_window.device = device

    # ------------------------------------------------------------------
    # Page Lifecycle
    # ------------------------------------------------------------------

    def on_enter(self, main_window) -> None:
        """Called when this page becomes active."""
        self._main_window = main_window
        self._scan_devices()

    def validate(self) -> bool:
        """Validate: at least one device must be selected."""
        if not self._devices:
            QMessageBox.warning(
                self, "No Device",
                "No device detected. Connect your device via USB and scan again."
            )
            return False

        row = self._device_table.currentRow()
        if row < 0:
            QMessageBox.warning(
                self, "No Device Selected",
                "Please select your device from the list."
            )
            return False

        return True
