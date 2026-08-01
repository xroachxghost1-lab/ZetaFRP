#!/usr/bin/env python3
"""
Zeta FRP Wizard — Interactive Bypass Guides
=============================================
Step-by-step visual guides for interactive FRP bypass
methods (TalkBack, emergency dialer, keyboard tricks).

These methods are mostly patched on modern devices but
remain useful for older Android versions and certain
manufacturers who lag on security updates.

ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
Unauthorised use, distribution, or reproduction is an act of war.
Copyright © 2026 Zeta Omniverse. All rights reserved.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

class GuideStep:
    """A single step in an interactive bypass guide."""
    def __init__(self, step_number: int, title: str, description: str,
                 image_hint: str = "", expected_screen: str = "",
                 action: str = ""):
        self.step_number = step_number
        self.title = title
        self.description = description
        self.image_hint = image_hint    # Description for screenshot
        self.expected_screen = expected_screen
        self.action = action

class InteractiveGuide:
    """Container for interactive bypass method guides."""

    @staticmethod
    def get_talkback_guide() -> List[GuideStep]:
        """
        TalkBack accessibility exploit guide.
        Works on: Samsung Android 12-13 (patched on One UI 5.0+)
        """
        return [
            GuideStep(1, "Start Setup",
                      "Begin the device setup wizard until you reach the 'Welcome' or 'Let's Go' screen.",
                      "Welcome screen with 'Start' or 'Let's Go' button"),
            GuideStep(2, "Enable TalkBack",
                      "Draw an 'L' shape on the screen with two fingers to activate TalkBack. "
                      "Alternatively, press and hold both volume buttons for 3 seconds.",
                      "TalkBack tutorial screen appears",
                      action="Draw 'L' with two fingers, OR hold Volume Up + Down for 3 seconds"),
            GuideStep(3, "Open TalkBack Settings",
                      "Once TalkBack is active, draw a 'V' shape on the screen to open TalkBack settings. "
                      "Or, tap the TalkBack icon and select 'TalkBack Settings'.",
                      "TalkBack settings menu"),
            GuideStep(4, "Access Help & Feedback",
                      "In TalkBack settings, find and tap 'Help & Feedback' or 'About'.",
                      "Help & Feedback screen"),
            GuideStep(5, "Open YouTube / Browser",
                      "Tap on 'Open YouTube' or 'Privacy Policy' link. This will launch the browser.",
                      "YouTube app or Chrome browser opens"),
            GuideStep(6, "Access Google Account",
                      "In the browser, navigate to google.com and sign in if needed. "
                      "Then type 'Settings' in the search bar and tap on a result that opens system settings.",
                      "Android Settings app opens"),
            GuideStep(7, "Navigate to Accounts",
                      "Go to Accounts > Google > Remove account. "
                      "This removes the FRP lock. Then factory reset the device.",
                      "Accounts settings with Google account listed",
                      action="Settings > Accounts > Google > Remove Account"),
            GuideStep(8, "Factory Reset",
                      "After removing the account, go to Settings > General Management > Reset > Factory Data Reset.",
                      "Factory reset confirmation screen",
                      action="Perform factory reset to complete FRP removal"),
        ]

    @staticmethod
    def get_emergency_dialer_guide() -> List[GuideStep]:
        """
        Emergency dialer exploit guide.
        Works on: Samsung, LG, Motorola (Android 10-13, patched on latest)
        """
        return [
            GuideStep(1, "Start Setup",
                      "Begin device setup until you reach the 'Connect to Wi-Fi' screen.",
                      "Wi-Fi connection screen"),
            GuideStep(2, "Open Emergency Call",
                      "Tap 'Emergency Call' at the bottom of the screen.",
                      "Emergency dialer keypad",
                      action="Tap 'Emergency Call'"),
            GuideStep(3, "Enter Code",
                      "Enter the secret code: *#0*# (Samsung) or *#*#4636#*#* (generic Android). "
                      "Different codes work on different devices.",
                      "Testing menu or Phone Information screen",
                      action="Enter code: *#0*# or *#*#4636#*#*"),
            GuideStep(4, "Access Settings",
                      "From the testing menu, navigate to settings or use the back button "
                      "to reach the app drawer / settings.",
                      "Settings accessible"),
            GuideStep(5, "Remove Account",
                      "Navigate to Accounts > Google > Remove account.",
                      "Account removed successfully",
                      action="Settings > Accounts > Remove Google account"),
            GuideStep(6, "Factory Reset",
                      "Perform factory reset from Settings to complete FRP removal.",
                      "Factory reset in progress"),
        ]

    @staticmethod
    def get_keyboard_hijack_guide() -> List[GuideStep]:
        """
        Keyboard settings hijack guide.
        Works on: Various Android 9-12 devices.
        """
        return [
            GuideStep(1, "Start Setup",
                      "Begin setup until you reach a text input field (e.g., Wi-Fi password or name entry).",
                      "Text input field visible"),
            GuideStep(2, "Long Press Keyboard",
                      "Long press on the spacebar or the microphone icon on the keyboard. "
                      "Select 'Keyboard Settings' or 'Language Settings'.",
                      "Keyboard settings popup",
                      action="Long press spacebar > Keyboard Settings"),
            GuideStep(3, "Open Help",
                      "In keyboard settings, find 'Help', 'About', or 'Privacy Policy'. "
                      "Tap to open in browser.",
                      "Browser opens"),
            GuideStep(4, "Download APK / Access Settings",
                      "In the browser, search for and download a settings shortcut app, "
                      "or navigate to a URL that triggers the Settings intent.",
                      "Settings opens or APK installs",
                      action="Search: 'settings shortcut app' or use intent:// URL"),
            GuideStep(5, "Remove Account & Reset",
                      "Navigate to Accounts > Google > Remove account, then factory reset.",
                      "FRP removed",
                      action="Settings > Accounts > Remove Google > Factory Reset"),
        ]
