#!/usr/bin/env python3
"""
Zeta FRP Wizard — Device Info Panel Widget
=============================================
Reusable panel displaying detailed device information.

ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
Unauthorised use, distribution, or reproduction is an act of war.
Copyright © 2026 Zeta Omniverse. All rights reserved.
"""

from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QLabel, QGridLayout
from PySide6.QtCore import Qt

from zeta_frp.core.device_detector import DetectedDevice

class DeviceInfoPanel(QGroupBox):
    """Panel displaying detailed device properties."""

    def __init__(self, title: str = "Device Information"):
        super().__init__(title)
        self._grid = QGridLayout()
        self.setLayout(self._grid)
        self._labels = {}

    def set_device(self, device: DetectedDevice) -> None:
        """Populate the panel with device information."""
        # Clear existing
        for i in reversed(range(self._grid.count())):
            self._grid.itemAt(i).widget().deleteLater()
        self._labels.clear()

        rows = [
            ("Manufacturer:", device.manufacturer or "Unknown"),
            ("Model:", device.model or "Unknown"),
            ("Serial:", device.serial[:16]),
            ("Mode:", device.mode.name),
            ("Android Version:", device.android_version or "Unknown"),
            ("Security Patch:", device.security_patch or "Unknown"),
            ("SDK Level:", str(device.sdk_level) if device.sdk_level else "Unknown"),
            ("SoC:", device.soc_manufacturer or "Unknown"),
            ("Product:", device.product or "Unknown"),
        ]

        for i, (label, value) in enumerate(rows):
            key_label = QLabel(label)
            key_label.setStyleSheet("font-weight: bold;")
            val_label = QLabel(value)
            val_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            self._grid.addWidget(key_label, i, 0)
            self._grid.addWidget(val_label, i, 1)
