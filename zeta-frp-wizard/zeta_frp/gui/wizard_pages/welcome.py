#!/usr/bin/env python3
"""
Zeta FRP Wizard — Welcome Page
=================================
First wizard page: welcome message, legal disclaimer,
and driver prerequisite check.

ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
Unauthorised use, distribution, or reproduction is an act of war.
Copyright © 2026 Zeta Omniverse. All rights reserved.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QCheckBox,
    QGroupBox, QScrollArea, QHBoxLayout, QTextEdit,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from zeta_frp.utils.logger import get_logger
from zeta_frp.drivers.driver_installer import DriverInstaller

logger = get_logger(__name__)

class WelcomePage(QWidget):
    """
    Welcome and prerequisites page.

    Displays:
    - Welcome message and tool overview
    - Legal disclaimer with mandatory acceptance
    - Driver installation status
    - Quick start guide
    """

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(16)

        # Title
        title = QLabel("Welcome to Zeta FRP Wizard")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel(
            "This wizard will guide you through removing Factory Reset Protection\n"
            "from your Android device. Follow each step carefully."
        )
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        # Quick start
        quick_group = QGroupBox("Before You Begin")
        quick_layout = QVBoxLayout(quick_group)
        quick_items = [
            "1. Ensure your device is charged (at least 50%)",
            "2. Use a quality USB cable (original cable recommended)",
            "3. Close other phone management software (Smart Switch, iTunes, etc.)",
            "4. Temporarily disable antivirus software (may interfere with flashing)",
            "5. Backup important data — FRP removal may wipe your device",
        ]
        for item in quick_items:
            quick_layout.addWidget(QLabel(item))
        layout.addWidget(quick_group)

        # Driver status
        driver_group = QGroupBox("USB Drivers Status")
        driver_layout = QVBoxLayout(driver_group)
        self._driver_labels = {}

        installer = DriverInstaller()
        for driver, installed in installer.check_drivers():
            hbox = QHBoxLayout()
            name_label = QLabel(driver)
            status_label = QLabel("✓ Installed" if installed else "⚠ Not Found")
            status_label.setObjectName(
                "driverOk" if installed else "driverWarning"
            )
            hbox.addWidget(name_label)
            hbox.addStretch()
            hbox.addWidget(status_label)
            driver_layout.addLayout(hbox)
            self._driver_labels[driver] = status_label

        install_btn = QPushButton("Install Missing Drivers")
        install_btn.clicked.connect(self._install_drivers)
        driver_layout.addWidget(install_btn)
        layout.addWidget(driver_group)

        # Legal disclaimer
        legal_group = QGroupBox("Legal Disclaimer")
        legal_layout = QVBoxLayout(legal_group)

        disclaimer = QTextEdit()
        disclaimer.setReadOnly(True)
        disclaimer.setMaximumHeight(120)
        disclaimer.setHtml(
            "<p><b>IMPORTANT LEGAL NOTICE:</b></p>"
            "<p>This tool is intended <b>ONLY</b> for legitimate device recovery by "
            "the rightful owner. Bypassing Factory Reset Protection on a device "
            "you do not own is illegal in most jurisdictions.</p>"
            "<p>By using this tool, you certify that:</p>"
            "<ul>"
            "<li>You are the legal owner of the device</li>"
            "<li>You have the right to remove FRP from this device</li>"
            "<li>You understand the risks, including potential data loss and device bricking</li>"
            "<li>You accept full responsibility for any consequences</li>"
            "</ul>"
        )
        legal_layout.addWidget(disclaimer)

        self._accept_check = QCheckBox(
            "I understand and accept the terms above. I am the legal owner of this device."
        )
        legal_layout.addWidget(self._accept_check)
        layout.addWidget(legal_group)

        layout.addStretch()

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self) -> bool:
        """Validate before proceeding. Requires disclaimer acceptance."""
        if not self._accept_check.isChecked():
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self, "Disclaimer Required",
                "You must accept the legal disclaimer before proceeding."
            )
            return False
        return True

    def _install_drivers(self) -> None:
        """Trigger driver installation."""
        installer = DriverInstaller()
        installer.install_all()

        # Refresh status
        for driver, installed in installer.check_drivers():
            if driver in self._driver_labels:
                self._driver_labels[driver].setText(
                    "✓ Installed" if installed else "⚠ Not Found"
                )
