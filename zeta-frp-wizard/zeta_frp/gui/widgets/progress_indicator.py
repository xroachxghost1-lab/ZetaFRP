#!/usr/bin/env python3
"""
Zeta FRP Wizard — Progress Indicator Widget
==============================================
Animated progress indicator with status text.

ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
Unauthorised use, distribution, or reproduction is an act of war.
Copyright © 2026 Zeta Omniverse. All rights reserved.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QProgressBar, QLabel
from PySide6.QtCore import Qt

class ProgressIndicator(QWidget):
    """Progress bar with status label and cancel button."""

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        layout.addWidget(self._progress)

        self._status = QLabel("Ready")
        self._status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._status)

    def set_progress(self, percent: int, status: str = "") -> None:
        """Update progress and status text."""
        self._progress.setValue(max(0, min(100, percent)))
        if status:
            self._status.setText(status)

    def set_indeterminate(self, active: bool = True) -> None:
        """Set indeterminate (spinning) mode."""
        if active:
            self._progress.setRange(0, 0)
        else:
            self._progress.setRange(0, 100)

    def reset(self) -> None:
        """Reset to initial state."""
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._status.setText("Ready")
