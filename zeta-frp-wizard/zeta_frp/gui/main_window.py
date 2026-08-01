#!/usr/bin/env python3
"""
Zeta FRP Wizard — Main Window
===============================
PySide6 QMainWindow hosting the wizard page stack.

ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
Unauthorised use, distribution, or reproduction is an act of war.
Copyright © 2026 Zeta Omniverse. All rights reserved.
"""

from PySide6.QtWidgets import (
    QMainWindow, QStackedWidget, QVBoxLayout, QWidget,
    QPushButton, QHBoxLayout, QLabel, QProgressBar,
    QMessageBox, QApplication,
)
from PySide6.QtCore import Qt, QSize, Signal, QThread, QTimer
from PySide6.QtGui import QIcon, QFont

from zeta_frp.gui.wizard_pages.welcome import WelcomePage
from zeta_frp.gui.wizard_pages.device_detect import DeviceDetectPage
from zeta_frp.gui.wizard_pages.method_select import MethodSelectPage
from zeta_frp.gui.wizard_pages.firmware_download import FirmwareDownloadPage
from zeta_frp.gui.wizard_pages.execution import ExecutionPage
from zeta_frp.gui.wizard_pages.verification import VerificationPage
from zeta_frp.utils.logger import get_logger
from zeta_frp.utils.config import ConfigManager

logger = get_logger(__name__)

class MainWindow(QMainWindow):
    """
    Main application window hosting the 6-step wizard.

    The wizard flow:
    1. Welcome / Prerequisites
    2. Device Detection
    3. Method Selection
    4. Firmware Download (optional)
    5. Execution
    6. Verification & Cleanup
    """

    # Signals for thread-safe UI updates
    device_detected_signal = Signal(object)  # DetectedDevice
    method_selected_signal = Signal(object)  # MethodAvailability
    progress_signal = Signal(int, str)       # percent, message
    log_signal = Signal(str)                 # log message
    step_complete_signal = Signal(int)       # step number

    WINDOW_TITLE = "Zeta FRP Wizard"
    WINDOW_MIN_SIZE = QSize(900, 650)

    def __init__(self, debug: bool = False):
        super().__init__()
        self._debug = debug
        self._current_step = 0
        self._device = None
        self._selected_method = None
        self._firmware_path = None

        self._setup_ui()
        self._connect_signals()
        self._load_config()

        logger.info("Main window initialized")

    # ------------------------------------------------------------------
    # UI Setup
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        """Build the main window UI."""
        self.setWindowTitle(self.WINDOW_TITLE)
        self.setMinimumSize(self.WINDOW_MIN_SIZE)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header bar
        header = self._create_header()
        main_layout.addWidget(header)

        # Step indicator
        self._step_indicator = self._create_step_indicator()
        main_layout.addWidget(self._step_indicator)

        # Page stack
        self._stack = QStackedWidget()
        self._stack.addWidget(WelcomePage())
        self._stack.addWidget(DeviceDetectPage())
        self._stack.addWidget(MethodSelectPage())
        self._stack.addWidget(FirmwareDownloadPage())
        self._stack.addWidget(ExecutionPage())
        self._stack.addWidget(VerificationPage())
        main_layout.addWidget(self._stack, stretch=1)

        # Navigation bar
        nav = self._create_navigation()
        main_layout.addWidget(nav)

        # Status bar
        self._status_bar = self.statusBar()
        self._status_label = QLabel("Ready")
        self._status_bar.addWidget(self._status_label)

    def _create_header(self) -> QWidget:
        """Create the header bar with logo and title."""
        header = QWidget()
        header.setObjectName("headerBar")
        header.setFixedHeight(56)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 8, 20, 8)

        title = QLabel("Zeta FRP Wizard")
        title.setObjectName("headerTitle")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)

        subtitle = QLabel("Universal Factory Reset Protection Removal")
        subtitle.setObjectName("headerSubtitle")

        layout.addWidget(title)
        layout.addSpacing(20)
        layout.addWidget(subtitle)
        layout.addStretch()

        return header

    def _create_step_indicator(self) -> QWidget:
        """Create the step progress indicator."""
        widget = QWidget()
        widget.setObjectName("stepIndicator")
        widget.setFixedHeight(48)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(20, 8, 20, 8)
        layout.setSpacing(0)

        self._step_labels = []
        steps = [
            "1. Welcome",
            "2. Detect Device",
            "3. Select Method",
            "4. Firmware",
            "5. Execute",
            "6. Verify",
        ]

        for i, text in enumerate(steps):
            label = QLabel(text)
            label.setObjectName(f"stepLabel_{i}")
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)
            self._step_labels.append(label)

            if i < len(steps) - 1:
                arrow = QLabel("→")
                arrow.setObjectName("stepArrow")
                layout.addWidget(arrow)

        return widget

    def _create_navigation(self) -> QWidget:
        """Create the navigation bar with Back/Next buttons."""
        nav = QWidget()
        nav.setObjectName("navBar")
        nav.setFixedHeight(56)
        layout = QHBoxLayout(nav)
        layout.setContentsMargins(20, 8, 20, 8)

        self._back_btn = QPushButton("← Back")
        self._back_btn.setObjectName("navBackBtn")
        self._back_btn.setEnabled(False)
        self._back_btn.clicked.connect(self._go_back)

        self._next_btn = QPushButton("Next →")
        self._next_btn.setObjectName("navNextBtn")
        self._next_btn.clicked.connect(self._go_next)

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setObjectName("navCancelBtn")
        self._cancel_btn.clicked.connect(self._cancel)

        layout.addWidget(self._cancel_btn)
        layout.addStretch()
        layout.addWidget(self._back_btn)
        layout.addSpacing(10)
        layout.addWidget(self._next_btn)

        return nav

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _go_next(self) -> None:
        """Advance to the next wizard step."""
        if self._current_step >= self._stack.count() - 1:
            return

        # Validate current step before proceeding
        current_page = self._stack.widget(self._current_step)
        if hasattr(current_page, "validate") and not current_page.validate():
            return

        self._current_step += 1
        self._update_navigation()
        self._stack.setCurrentIndex(self._current_step)
        self._update_step_indicator()
        self._on_step_entered(self._current_step)

    def _go_back(self) -> None:
        """Go back to the previous wizard step."""
        if self._current_step <= 0:
            return
        self._current_step -= 1
        self._update_navigation()
        self._stack.setCurrentIndex(self._current_step)
        self._update_step_indicator()

    def _cancel(self) -> None:
        """Cancel the wizard."""
        reply = QMessageBox.question(
            self, "Cancel Wizard",
            "Are you sure you want to cancel? Any progress will be lost.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.close()

    def _update_navigation(self) -> None:
        """Update navigation button states."""
        self._back_btn.setEnabled(self._current_step > 0)
        is_last = self._current_step >= self._stack.count() - 1
        self._next_btn.setText("Finish" if is_last else "Next →")

    def _update_step_indicator(self) -> None:
        """Update step indicator highlighting."""
        for i, label in enumerate(self._step_labels):
            if i < self._current_step:
                label.setObjectName(f"stepLabel_{i}_done")
            elif i == self._current_step:
                label.setObjectName(f"stepLabel_{i}_active")
            else:
                label.setObjectName(f"stepLabel_{i}")
            label.style().unpolish(label)
            label.style().polish(label)

    def _on_step_entered(self, step: int) -> None:
        """Called when entering a new wizard step."""
        page = self._stack.widget(step)
        if hasattr(page, "on_enter"):
            page.on_enter(self)

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        self.device_detected_signal.connect(self._on_device_detected)
        self.method_selected_signal.connect(self._on_method_selected)
        self.progress_signal.connect(self._on_progress)
        self.log_signal.connect(self._on_log)
        self.step_complete_signal.connect(self._on_step_complete)

    def _on_device_detected(self, device) -> None:
        self._device = device
        self._status_label.setText(f"Device: {device.display_name}")

    def _on_method_selected(self, method) -> None:
        self._selected_method = method

    def _on_progress(self, percent: int, message: str) -> None:
        self._status_label.setText(f"{message} ({percent}%)")

    def _on_log(self, message: str) -> None:
        logger.info(message)

    def _on_step_complete(self, step: int) -> None:
        pass

    # ------------------------------------------------------------------
    # Config
    # ------------------------------------------------------------------

    def _load_config(self) -> None:
        """Load application configuration."""
        self._config = ConfigManager()
        self._config.load()

    # ------------------------------------------------------------------
    # Public Properties
    # ------------------------------------------------------------------

    @property
    def device(self):
        return self._device

    @device.setter
    def device(self, value):
        self._device = value
        self.device_detected_signal.emit(value)

    @property
    def selected_method(self):
        return self._selected_method

    @selected_method.setter
    def selected_method(self, value):
        self._selected_method = value
        self.method_selected_signal.emit(value)

    @property
    def firmware_path(self):
        return self._firmware_path

    @firmware_path.setter
    def firmware_path(self, value):
        self._firmware_path = value
