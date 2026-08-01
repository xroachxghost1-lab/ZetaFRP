#!/usr/bin/env python3
"""
Zeta FRP Wizard — Log Viewer Widget
======================================
Reusable scrolling log viewer with auto-scroll.

ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
Unauthorised use, distribution, or reproduction is an act of war.
Copyright © 2026 Zeta Omniverse. All rights reserved.
"""

from PySide6.QtWidgets import QTextEdit, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt

class LogViewer(QWidget):
    """Scrolling log output widget with clear and save controls."""

    MAX_LINES = 5000

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Controls
        ctrl_layout = QHBoxLayout()
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear)
        save_btn = QPushButton("Save Log...")
        save_btn.clicked.connect(self.save)
        ctrl_layout.addStretch()
        ctrl_layout.addWidget(clear_btn)
        ctrl_layout.addWidget(save_btn)
        layout.addLayout(ctrl_layout)

        # Text area
        self._text = QTextEdit()
        self._text.setReadOnly(True)
        self._text.setLineWrapMode(QTextEdit.NoWrap)
        self._text.setStyleSheet(
            "QTextEdit { background-color: #1a1a2e; color: #e0e0e0; "
            "font-family: 'Consolas', 'Courier New', monospace; font-size: 12px; }"
        )
        layout.addWidget(self._text)

        self._line_count = 0

    def append(self, text: str) -> None:
        """Append a line to the log. Auto-truncates old lines."""
        self._text.append(text)
        self._line_count += 1

        if self._line_count > self.MAX_LINES:
            # Remove oldest 1000 lines
            cursor = self._text.textCursor()
            cursor.movePosition(cursor.Start)
            for _ in range(1000):
                cursor.movePosition(cursor.Down, cursor.KeepAnchor)
            cursor.removeSelectedText()
            self._line_count -= 1000

        # Auto-scroll to bottom
        scrollbar = self._text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear(self) -> None:
        """Clear all log output."""
        self._text.clear()
        self._line_count = 0

    def save(self) -> None:
        """Save log to file."""
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Log", "zeta-frp-log.txt", "Text Files (*.txt *.log)"
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self._text.toPlainText())
