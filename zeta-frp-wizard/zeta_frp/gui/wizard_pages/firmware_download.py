#!/usr/bin/env python3
"""
Zeta FRP Wizard — Firmware Download Page
===========================================
Auto-downloads or accepts user-provided firmware
for flashing-based bypass methods.

ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
Unauthorised use, distribution, or reproduction is an act of war.
Copyright © 2026 Zeta Omniverse. All rights reserved.
"""

from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QGroupBox,
    QHBoxLayout, QProgressBar, QFileDialog, QRadioButton,
    QButtonGroup, QLineEdit, QMessageBox,
)
from PySide6.QtCore import Qt, QThread, Signal

from zeta_frp.firmware.downloader import FirmwareDownloader, DownloadProgress
from zeta_frp.utils.logger import get_logger

logger = get_logger(__name__)

class DownloadThread(QThread):
    """Background thread for firmware downloading."""
    progress = Signal(int, int, str)  # downloaded, total, filename
    complete = Signal(str)            # filepath
    error = Signal(str)

    def __init__(self, model: str, manufacturer: str):
        super().__init__()
        self._model = model
        self._manufacturer = manufacturer

    def run(self):
        try:
            downloader = FirmwareDownloader()

            def progress_cb(prog: DownloadProgress):
                self.progress.emit(prog.bytes_downloaded, prog.total_bytes, prog.filename)

            result = downloader.download(
                self._model, self._manufacturer,
                progress_callback=progress_cb,
            )
            if result:
                self.complete.emit(result)
            else:
                self.error.emit("Firmware not found. Try manual download.")
        except Exception as e:
            self.error.emit(str(e))

class FirmwareDownloadPage(QWidget):
    """
    Firmware acquisition wizard page.

    Options:
    1. Auto-download from Samsung Kies / Xiaomi Updater / community
    2. Provide firmware file manually
    3. Skip (for non-flashing methods)
    """

    def __init__(self):
        super().__init__()
        self._main_window = None
        self._download_thread = None
        self._firmware_path = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(16)

        title = QLabel("Firmware Acquisition")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        # Method selection
        method_group = QGroupBox("Firmware Source")
        method_layout = QVBoxLayout(method_group)
        self._method_group = QButtonGroup()

        auto_radio = QRadioButton("Auto-download firmware from official servers")
        self._method_group.addButton(auto_radio, 0)
        method_layout.addWidget(auto_radio)

        manual_radio = QRadioButton("I have the firmware file (manual selection)")
        self._method_group.addButton(manual_radio, 1)
        method_layout.addWidget(manual_radio)

        skip_radio = QRadioButton("Skip (not needed for this method)")
        self._method_group.addButton(skip_radio, 2)
        method_layout.addWidget(skip_radio)

        auto_radio.setChecked(True)
        layout.addWidget(method_group)

        # Auto download section
        auto_group = QGroupBox("Automatic Download")
        auto_layout = QVBoxLayout(auto_group)

        self._auto_status = QLabel("Ready to download firmware from official sources.")
        self._auto_status.setWordWrap(True)
        auto_layout.addWidget(self._auto_status)

        self._dl_progress = QProgressBar()
        self._dl_progress.setVisible(False)
        auto_layout.addWidget(self._dl_progress)

        self._dl_btn = QPushButton("📥 Start Download")
        self._dl_btn.setObjectName("primaryBtn")
        self._dl_btn.clicked.connect(self._start_download)
        auto_layout.addWidget(self._dl_btn)

        layout.addWidget(auto_group)

        # Manual firmware section
        manual_group = QGroupBox("Manual Firmware Selection")
        manual_layout = QVBoxLayout(manual_group)

        file_layout = QHBoxLayout()
        self._file_path = QLineEdit()
        self._file_path.setPlaceholderText("Path to firmware file...")
        file_layout.addWidget(self._file_path)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_firmware)
        file_layout.addWidget(browse_btn)

        manual_layout.addLayout(file_layout)
        layout.addWidget(manual_group)

        # Info
        info_label = QLabel(
            "<b>Note:</b> Firmware download requires internet connection. "
            "Large files (1-5 GB) may take 10-30 minutes depending on your connection speed."
        )
        info_label.setWordWrap(True)
        info_label.setObjectName("helpText")
        layout.addWidget(info_label)

        layout.addStretch()

    # ------------------------------------------------------------------
    # Page Lifecycle
    # ------------------------------------------------------------------

    def on_enter(self, main_window) -> None:
        self._main_window = main_window
        method = main_window.selected_method

        if method:
            self._auto_status.setText(
                f"Selected method: {method.name}\n"
                f"Device: {main_window.device.display_name if main_window.device else 'Unknown'}"
            )

    # ------------------------------------------------------------------
    # Download Logic
    # ------------------------------------------------------------------

    def _start_download(self) -> None:
        """Start auto-download in background thread."""
        device = self._main_window.device if self._main_window else None
        if not device:
            QMessageBox.warning(self, "No Device", "Device information not available.")
            return

        self._dl_btn.setEnabled(False)
        self._dl_progress.setVisible(True)
        self._dl_progress.setRange(0, 100)

        self._download_thread = DownloadThread(device.model, device.manufacturer)
        self._download_thread.progress.connect(self._on_dl_progress)
        self._download_thread.complete.connect(self._on_dl_complete)
        self._download_thread.error.connect(self._on_dl_error)
        self._download_thread.start()

    def _on_dl_progress(self, downloaded: int, total: int, filename: str) -> None:
        """Update download progress bar."""
        if total > 0:
            percent = int((downloaded / total) * 100)
            self._dl_progress.setValue(percent)
            self._auto_status.setText(f"Downloading {filename}... ({percent}%)")

    def _on_dl_complete(self, filepath: str) -> None:
        """Download completed."""
        self._dl_btn.setEnabled(True)
        self._dl_progress.setVisible(False)
        self._firmware_path = filepath
        if self._main_window:
            self._main_window.firmware_path = filepath
        self._auto_status.setText(f"✅ Download complete: {Path(filepath).name}")
        QMessageBox.information(self, "Download Complete", f"Firmware downloaded:\n{filepath}")

    def _on_dl_error(self, error: str) -> None:
        """Download failed."""
        self._dl_btn.setEnabled(True)
        self._dl_progress.setVisible(False)
        self._auto_status.setText(f"❌ Download failed: {error}")
        QMessageBox.warning(self, "Download Failed", error)

    def _browse_firmware(self) -> None:
        """Open file dialog for manual firmware selection."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Firmware File",
            "", "Firmware Files (*.tar *.md5 *.zip *.img *.elf *.bin);;All Files (*.*)"
        )
        if path:
            self._file_path.setText(path)
            self._firmware_path = path
            if self._main_window:
                self._main_window.firmware_path = path

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self) -> bool:
        """Validate based on selected method."""
        choice = self._method_group.checkedId()

        if choice == 2:  # Skip
            return True

        if choice == 1:  # Manual
            path = self._file_path.text().strip()
            if not path or not Path(path).exists():
                QMessageBox.warning(
                    self, "Firmware Required",
                    "Please select a valid firmware file."
                )
                return False
            return True

        # Auto-download
        if not self._firmware_path:
            reply = QMessageBox.question(
                self, "No Firmware Downloaded",
                "Firmware has not been downloaded yet. Continue anyway?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            return reply == QMessageBox.Yes

        return True
