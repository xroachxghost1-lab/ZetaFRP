#!/usr/bin/env python3
"""
Zeta FRP Wizard — Verification Page
======================================
Final verification and cleanup after FRP bypass.

ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
Unauthorised use, distribution, or reproduction is an act of war.
Copyright © 2026 Zeta Omniverse. All rights reserved.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QGroupBox,
    QCheckBox, QTextEdit,
)
from PySide6.QtCore import Qt

from zeta_frp.utils.logger import get_logger

logger = get_logger(__name__)

class VerificationPage(QWidget):
    """
    Verification and cleanup page.

    Final step of the wizard:
    - Verify FRP is removed
    - Optionally flash stock firmware back
    - Save session log
    - Get support links
    """

    def __init__(self):
        super().__init__()
        self._main_window = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(16)

        title = QLabel("Verification & Cleanup")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        # Success message
        success_group = QGroupBox("Bypass Complete")
        success_layout = QVBoxLayout(success_group)

        success_label = QLabel(
            "✅ FRP bypass has been executed!\n\n"
            "Follow these final steps to ensure everything is working:"
        )
        success_label.setWordWrap(True)
        success_layout.addWidget(success_label)

        checklist = [
            "☐ Device boots to the home screen without Google verification",
            "☐ You can sign in with a new Google account",
            "☐ All device features are working (WiFi, Bluetooth, calls)",
            "☐ Samsung/Manufacturer account is not locked (if applicable)",
        ]
        for item in checklist:
            success_layout.addWidget(QLabel(item))

        layout.addWidget(success_group)

        # Optional cleanup
        cleanup_group = QGroupBox("Post-Bypass Options")
        cleanup_layout = QVBoxLayout(cleanup_group)

        self._flash_stock_check = QCheckBox(
            "Flash stock firmware back (recommended if combination firmware was used)"
        )
        cleanup_layout.addWidget(self._flash_stock_check)

        self._save_log_check = QCheckBox("Save execution log to file")
        self._save_log_check.setChecked(True)
        cleanup_layout.addWidget(self._save_log_check)

        layout.addWidget(cleanup_group)

        # Summary
        summary_group = QGroupBox("Session Summary")
        summary_layout = QVBoxLayout(summary_group)

        self._summary_text = QTextEdit()
        self._summary_text.setReadOnly(True)
        self._summary_text.setMaximumHeight(120)
        summary_layout.addWidget(self._summary_text)

        layout.addWidget(summary_group)

        # Support
        support_label = QLabel(
            "<b>Need help?</b><br>"
            "• Visit XDA Developers forums for device-specific guides<br>"
            "• Check the Zeta FRP Wizard GitHub repository for updates<br>"
            "• Report issues on GitHub with your device model and log file"
        )
        support_label.setWordWrap(True)
        support_label.setObjectName("helpText")
        layout.addWidget(support_label)

        layout.addStretch()

    # ------------------------------------------------------------------
    # Page Lifecycle
    # ------------------------------------------------------------------

    def on_enter(self, main_window) -> None:
        self._main_window = main_window

        # Build summary
        device = main_window.device
        method = main_window.selected_method
        firmware = main_window.firmware_path

        summary = "=== Zeta FRP Wizard Session Summary ===\n\n"
        if device:
            summary += f"Device: {device.display_name}\n"
            summary += f"Model: {device.model}\n"
            summary += f"Android: {device.android_version}\n"
            summary += f"Security Patch: {device.security_patch}\n"
        if method:
            summary += f"Method: {method.name}\n"
        if firmware:
            summary += f"Firmware: {firmware}\n"

        summary += "\nZeta Omniverse — Alpha's Empire\n"
        summary += "Copyright © 2026. All rights reserved."

        self._summary_text.setText(summary)

    def validate(self) -> bool:
        return True  # Last page, no validation needed
