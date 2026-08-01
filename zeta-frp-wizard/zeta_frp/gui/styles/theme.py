#!/usr/bin/env python3
"""
Zeta FRP Wizard — Application Theme
=====================================
Dark professional theme with Zeta branding.
Blue accent (#4d6bfe), dark backgrounds, clean typography.

ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
Unauthorised use, distribution, or reproduction is an act of war.
Copyright © 2026 Zeta Omniverse. All rights reserved.
"""

def get_stylesheet() -> str:
    """Return the complete application QSS stylesheet."""
    return """
    /* ================================================================
       ZETA FRP WIZARD — Professional Dark Theme
       Copyright © 2026 Zeta Omniverse. All rights reserved.
       ================================================================ */

    /* --- Global --- */
    QWidget {
        background-color: #1a1a2e;
        color: #e0e0e0;
        font-family: 'Segoe UI', 'SF Pro Display', 'Roboto', sans-serif;
        font-size: 13px;
    }

    /* --- Header --- */
    #headerBar {
        background-color: #16162b;
        border-bottom: 2px solid #4d6bfe;
    }
    #headerTitle {
        color: #ffffff;
        font-size: 16px;
    }
    #headerSubtitle {
        color: #8888aa;
        font-size: 12px;
    }

    /* --- Step Indicator --- */
    #stepIndicator {
        background-color: #1e1e36;
        border-bottom: 1px solid #2a2a4a;
    }
    QLabel[id^="stepLabel"] {
        color: #666688;
        font-size: 12px;
        padding: 4px 8px;
        border-radius: 4px;
    }
    QLabel[id$="_active"] {
        color: #ffffff;
        background-color: #4d6bfe;
        font-weight: bold;
    }
    QLabel[id$="_done"] {
        color: #4CAF50;
    }
    #stepArrow {
        color: #444466;
        font-size: 14px;
    }

    /* --- Navigation --- */
    #navBar {
        background-color: #16162b;
        border-top: 1px solid #2a2a4a;
    }
    #navBackBtn, #navCancelBtn {
        background-color: transparent;
        color: #8888aa;
        border: 1px solid #444466;
        padding: 8px 20px;
        border-radius: 6px;
    }
    #navBackBtn:hover, #navCancelBtn:hover {
        background-color: #2a2a4a;
        color: #ffffff;
    }
    #navNextBtn {
        background-color: #4d6bfe;
        color: #ffffff;
        border: none;
        padding: 8px 24px;
        border-radius: 6px;
        font-weight: bold;
    }
    #navNextBtn:hover {
        background-color: #3d5be0;
    }
    #navNextBtn:disabled {
        background-color: #333355;
        color: #666688;
    }

    /* --- Buttons --- */
    #primaryBtn {
        background-color: #4d6bfe;
        color: #ffffff;
        border: none;
        padding: 10px 24px;
        border-radius: 8px;
        font-weight: bold;
        font-size: 14px;
    }
    #primaryBtn:hover {
        background-color: #3d5be0;
    }
    #primaryBtn:disabled {
        background-color: #333355;
        color: #666688;
    }

    QPushButton {
        background-color: #2a2a4a;
        color: #e0e0e0;
        border: 1px solid #3a3a5a;
        padding: 6px 16px;
        border-radius: 6px;
    }
    QPushButton:hover {
        background-color: #3a3a5a;
    }

    /* --- Group Boxes --- */
    QGroupBox {
        border: 1px solid #2a2a4a;
        border-radius: 8px;
        margin-top: 12px;
        padding-top: 20px;
        font-weight: bold;
        color: #aaaacc;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 4px 12px;
        background-color: #1a1a2e;
    }

    /* --- Input Fields --- */
    QLineEdit, QTextEdit, QPlainTextEdit {
        background-color: #0f0f23;
        border: 1px solid #3a3a5a;
        border-radius: 6px;
        padding: 8px;
        color: #e0e0e0;
    }
    QLineEdit:focus, QTextEdit:focus {
        border-color: #4d6bfe;
    }

    /* --- Progress Bar --- */
    QProgressBar {
        background-color: #0f0f23;
        border: 1px solid #3a3a5a;
        border-radius: 6px;
        text-align: center;
        height: 20px;
    }
    QProgressBar::chunk {
        background-color: #4d6bfe;
        border-radius: 5px;
    }

    /* --- Radio & Checkboxes --- */
    QRadioButton, QCheckBox {
        spacing: 8px;
        color: #ccccdd;
    }
    QRadioButton::indicator, QCheckBox::indicator {
        width: 18px;
        height: 18px;
    }

    /* --- Scroll Area --- */
    QScrollArea {
        border: none;
        background-color: transparent;
    }
    QScrollBar:vertical {
        background-color: #1a1a2e;
        width: 10px;
        border-radius: 5px;
    }
    QScrollBar::handle:vertical {
        background-color: #3a3a5a;
        border-radius: 5px;
        min-height: 30px;
    }
    QScrollBar::handle:vertical:hover {
        background-color: #4d6bfe;
    }

    /* --- Table --- */
    QTableWidget {
        background-color: #0f0f23;
        border: 1px solid #2a2a4a;
        border-radius: 6px;
        gridline-color: #2a2a4a;
    }
    QTableWidget::item:selected {
        background-color: #4d6bfe;
    }
    QHeaderView::section {
        background-color: #16162b;
        color: #aaaacc;
        border: none;
        padding: 8px;
        font-weight: bold;
    }

    /* --- Help Text --- */
    #helpText {
        color: #8888aa;
        font-size: 12px;
        font-style: italic;
    }

    /* --- Driver Status --- */
    #driverOk {
        color: #4CAF50;
        font-weight: bold;
    }
    #driverWarning {
        color: #FF9800;
        font-weight: bold;
    }

    /* --- Page Title --- */
    #pageTitle {
        font-size: 18px;
        font-weight: bold;
        color: #ffffff;
        padding-bottom: 4px;
        border-bottom: 2px solid #4d6bfe;
    }
    """
