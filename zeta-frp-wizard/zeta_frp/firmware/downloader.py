#!/usr/bin/env python3
"""
Zeta FRP Wizard — Firmware Download Manager
=============================================
Multi-source aggregator that downloads firmware from
Samsung Kies, Xiaomi Firmware Updater, XDA, and community sources.

ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
Unauthorised use, distribution, or reproduction is an act of war.
Copyright © 2026 Zeta Omniverse. All rights reserved.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Callable
from dataclasses import dataclass

from zeta_frp.utils.logger import get_logger
from zeta_frp.firmware.sources.samsung_kies import SamsungKiesSource
from zeta_frp.firmware.sources.xiaomi_updater import XiaomiUpdaterSource
from zeta_frp.firmware.sources.xda_firmware import XDAFirmwareSource
from zeta_frp.firmware.sources.motorola_lmsa import MotorolaLMSASource
from zeta_frp.firmware.validator import FirmwareValidator

logger = get_logger(__name__)

@dataclass
class DownloadProgress:
    """Progress information for firmware download."""
    source: str
    filename: str
    bytes_downloaded: int
    total_bytes: int
    percent: float
    speed_mbps: float
    status: str  # "downloading", "verifying", "complete", "error"

class FirmwareDownloader:
    """
    Multi-source firmware download manager.

    Aggregates firmware from multiple sources and automatically
    selects the best source based on device manufacturer.

    Usage:
        dl = FirmwareDownloader()
        path = dl.download(model="SM-G991B", manufacturer="samsung",
                          progress_callback=my_callback)
    """

    def __init__(self, download_dir: Optional[str] = None):
        if download_dir:
            self._download_dir = Path(download_dir)
        else:
            self._download_dir = Path.home() / "ZetaFRP" / "firmware"
        self._download_dir.mkdir(parents=True, exist_ok=True)

        self._sources = {
            "samsung": SamsungKiesSource(self._download_dir),
            "xiaomi": XiaomiUpdaterSource(self._download_dir),
            "xda": XDAFirmwareSource(self._download_dir),
            "motorola": MotorolaLMSASource(self._download_dir),
        }
        self._validator = FirmwareValidator()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def download(self, model: str, manufacturer: str,
                 csc: str = "AUTO", imei: Optional[str] = None,
                 progress_callback: Optional[Callable[[DownloadProgress], None]] = None
                 ) -> Optional[str]:
        """
        Download firmware for a specific device model.

        Args:
            model: Device model number (e.g., SM-G991B)
            manufacturer: Manufacturer name (e.g., samsung)
            csc: CSC/region code (Samsung only)
            imei: IMEI for Samsung's validation requirement
            progress_callback: Called with DownloadProgress updates

        Returns:
            Path to downloaded firmware file, or None if download failed.
        """
        man_lower = manufacturer.lower()

        # Select source based on manufacturer
        source = None
        for key, src in self._sources.items():
            if key in man_lower:
                source = src
                break

        if source is None:
            # Fallback to XDA for unknown manufacturers
            source = self._sources["xda"]

        logger.info(f"Downloading firmware for {model} ({manufacturer}) from {source.name}")

        # Search for firmware
        if progress_callback:
            progress_callback(DownloadProgress(
                source=source.name, filename="", bytes_downloaded=0,
                total_bytes=0, percent=0, speed_mbps=0, status="downloading",
            ))

        result = source.download(model, csc=csc, imei=imei,
                                 progress_callback=progress_callback)

        if result is None:
            logger.warning(f"Firmware not found on {source.name}, trying fallback sources...")
            # Try XDA as fallback
            result = self._sources["xda"].download(
                model, manufacturer=manufacturer,
                progress_callback=progress_callback,
            )

        if result is None:
            logger.error(f"Firmware not found for {model} on any source")
            return None

        # Validate downloaded firmware
        if progress_callback:
            progress_callback(DownloadProgress(
                source=source.name, filename=Path(result).name,
                bytes_downloaded=0, total_bytes=0, percent=100,
                speed_mbps=0, status="verifying",
            ))

        if self._validator.validate(result, model, manufacturer):
            logger.info(f"Firmware validated: {result}")
            return result
        else:
            logger.error(f"Firmware validation failed for {result}")
            return None

    def search(self, model: str, manufacturer: str) -> list:
        """
        Search for available firmware without downloading.

        Returns:
            List of dicts with firmware info (source, version, size, url).
        """
        man_lower = manufacturer.lower()
        results = []

        for key, source in self._sources.items():
            if key in man_lower or key == "xda":
                try:
                    info = source.search(model, manufacturer)
                    if info:
                        results.append(info)
                except Exception as e:
                    logger.debug(f"Search failed on {source.name}: {e}")

        return results

    def get_download_dir(self) -> str:
        """Get the configured download directory."""
        return str(self._download_dir)

    def set_download_dir(self, path: str) -> None:
        """Set the download directory."""
        self._download_dir = Path(path)
        self._download_dir.mkdir(parents=True, exist_ok=True)
        for source in self._sources.values():
            source.set_download_dir(self._download_dir)
