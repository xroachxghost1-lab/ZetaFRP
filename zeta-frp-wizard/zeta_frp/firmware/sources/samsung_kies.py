#!/usr/bin/env python3
"""
Zeta FRP Wizard — Samsung Kies Firmware Source
================================================
Downloads Samsung firmware from Kies/FUS servers.

ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
Unauthorised use, distribution, or reproduction is an act of war.
Copyright © 2026 Zeta Omniverse. All rights reserved.
"""

from pathlib import Path
from typing import Optional, Callable, Dict

from zeta_frp.utils.logger import get_logger

logger = get_logger(__name__)

class SamsungKiesSource:
    """Samsung Kies/FUS firmware download source."""

    name = "Samsung Kies/FUS"

    def __init__(self, download_dir: Path):
        self._download_dir = download_dir

    def download(self, model: str, csc: str = "AUTO",
                 imei: Optional[str] = None,
                 progress_callback=None) -> Optional[str]:
        """
        Download Samsung firmware via Kies/FUS.
        Delegates to SamsungFirmwareDownloader.
        """
        from zeta_frp.plugins.samsung.download_frija import SamsungFirmwareDownloader

        downloader = SamsungFirmwareDownloader(str(self._download_dir))
        info = downloader.search_firmware(model, csc=csc, imei=imei)

        if info is None:
            return None

        return downloader.download_firmware(info, progress_callback=progress_callback)

    def search(self, model: str, manufacturer: str = "samsung") -> Optional[Dict]:
        """Search for firmware info without downloading."""
        from zeta_frp.plugins.samsung.download_frija import SamsungFirmwareDownloader

        downloader = SamsungFirmwareDownloader(str(self._download_dir))
        info = downloader.search_firmware(model)

        if info:
            return {
                "source": self.name,
                "model": info.model,
                "version": info.version,
                "size_bytes": info.size_bytes,
                "filename": info.filename,
                "csc": info.csc,
            }
        return None

    def set_download_dir(self, path: Path) -> None:
        self._download_dir = path
