#!/usr/bin/env python3
"""
Zeta FRP Wizard — Method Selection Page
==========================================
Displays available FRP bypass methods for the detected
device, ranked by risk and success probability.

ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
Unauthorised use, distribution, or reproduction is an act of war.
Copyright © 2026 Zeta Omniverse. All rights reserved.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QGroupBox,
    QHBoxLayout, QRadioButton, QButtonGroup, QScrollArea,
    QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from zeta_frp.core.method_engine import MethodEngine
from zeta_frp.core.spl_checker import MethodAvailability
from zeta_frp.utils.logger import get_logger

logger = get_logger(__name__)

class MethodSelectPage(QWidget):
    """
    Method selection wizard page.

    Shows all available methods with:
    - Risk level (color-coded)
    - Success probability
    - Requirements (USB debugging, bootloader, etc.)
    - Estimated time
    """

    RISK_COLORS = {
        "low": "#4CAF50",
        "medium": "#FF9800",
        "high": "#F44336",
        "critical": "#B71C1C",
    }

    def __init__(self):
        super().__init__()
        self._methods = []
        self._main_window = None
        self._selected_method = None
        self._radio_group = QButtonGroup()
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(16)

        title = QLabel("Select Bypass Method")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        instructions = QLabel(
            "Based on your device's Security Patch Level and properties,\n"
            "the following methods are available. Methods are sorted by safety."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Scrollable method list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self._methods_widget = QWidget()
        self._methods_layout = QVBoxLayout(self._methods_widget)
        self._methods_layout.setSpacing(10)
        scroll.setWidget(self._methods_widget)
        layout.addWidget(scroll, stretch=1)

        # Auto-select recommended
        self._auto_btn = QPushButton("✨ Use Recommended Method")
        self._auto_btn.setObjectName("primaryBtn")
        self._auto_btn.clicked.connect(self._select_recommended)
        layout.addWidget(self._auto_btn)

        layout.addStretch()

    # ------------------------------------------------------------------
    # Page Lifecycle
    # ------------------------------------------------------------------

    def on_enter(self, main_window) -> None:
        """Populate methods when page becomes active."""
        self._main_window = main_window
        device = main_window.device

        if device is None:
            return

        engine = MethodEngine()
        self._methods = engine.get_all_methods_for_device(device)
        self._populate_methods()

        # Auto-select recommended
        self._select_recommended()

    def _populate_methods(self) -> None:
        """Create method cards for each available method."""
        # Clear existing
        while self._methods_layout.count():
            child = self._methods_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self._radio_group = QButtonGroup()

        for method in self._methods:
            card = self._create_method_card(method)
            self._methods_layout.addWidget(card)

        self._methods_layout.addStretch()

    def _create_method_card(self, method: MethodAvailability) -> QWidget:
        """Create a card widget for a single method."""
        card = QGroupBox()
        card_layout = QVBoxLayout(card)

        # Header row: radio + name + risk badge
        header_layout = QHBoxLayout()
        radio = QRadioButton()
        self._radio_group.addButton(radio)
        header_layout.addWidget(radio)

        name_label = QLabel(method.name)
        name_font = QFont()
        name_font.setBold(True)
        name_label.setFont(name_font)
        header_layout.addWidget(name_label)

        header_layout.addStretch()

        risk_label = QLabel(f" {method.risk_level.upper()} ")
        risk_label.setStyleSheet(
            f"background-color: {self.RISK_COLORS.get(method.risk_level, '#888')};"
            f"color: white; padding: 4px 12px; border-radius: 4px; font-weight: bold;"
        )
        header_layout.addWidget(risk_label)

        card_layout.addLayout(header_layout)

        # Description
        desc = QLabel(method.description)
        desc.setWordWrap(True)
        card_layout.addWidget(desc)

        # Requirements
        reqs = []
        if method.requires_usb_debugging:
            reqs.append("⚠ Requires USB Debugging (pre-enabled)")
        if method.requires_unlocked_bootloader:
            reqs.append("⚠ Requires Unlocked Bootloader")
        if method.patched_after_spl:
            reqs.append(f"📅 Patched after SPL: {method.patched_after_spl}")

        if reqs:
            req_label = QLabel("\n".join(reqs))
            req_label.setStyleSheet("color: #FFA000; font-size: 12px;")
            card_layout.addWidget(req_label)

        return card

    # ------------------------------------------------------------------
    # Selection
    # ------------------------------------------------------------------

    def _select_recommended(self) -> None:
        """Select the first (recommended/lowest risk) method."""
        buttons = self._radio_group.buttons()
        if buttons:
            buttons[0].setChecked(True)

    def validate(self) -> bool:
        """Validate that a method is selected."""
        checked = self._radio_group.checkedButton()
        if checked is None:
            QMessageBox.warning(
                self, "No Method Selected",
                "Please select a bypass method."
            )
            return False

        idx = self._radio_group.buttons().index(checked)
        if 0 <= idx < len(self._methods):
            self._selected_method = self._methods[idx]
            if self._main_window:
                self._main_window.selected_method = self._selected_method
            return True

        return False
