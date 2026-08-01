#!/usr/bin/env python3
"""
Zeta FRP Wizard — Xiaomi Firmware Updater Source
==================================================
Downloads Xiaomi firmware from Xiaomi Firmware Updater API
and official Xiaomi servers.

API: https://xiaomifirmwareupdater.com/

ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
Unauthorised use, distribution, or reproduction is an act of war.
Copyright © 2026 Zeta Omniverse. All rights reserved.
"""

import requests
from pathlib import Path
from typing import Optional, Callable, Dict

from zeta_frp.utils.logger import get_logger

logger = get_logger(__name__)

class XiaomiUpdaterSource:
    """Xiaomi Firmware Updater download source."""

    name = "Xiaomi Firmware Updater"
    API_BASE = "https://raw.githubusercontent.com/XiaomiFirmwareUpdater"
    MIRROR_BASE = "https://bigota.d.miui.com"

    def __init__(self, download_dir: Path):
        self._download_dir = download_dir
        self._session = requests.Session()

    def download(self, model: str, csc: str = "",
                 imei: Optional[str] = None,
                 progress_callback=None) -> Optional[str]:
        """
        Download Xiaomi firmware.

        Xiaomi uses codenames (e.g., 'veux', 'lisa') rather than
        model numbers in their firmware API. The model number
        must be converted to a codename first.
        """
        codename = self._model_to_codename(model)
        if not codename:
            logger.error(f"Cannot find Xiaomi codename for model: {model}")
            return None

        # Try fastboot ROM (preferred for FRP bypass)
        url = self._get_latest_fastboot_url(codename)
        if not url:
            # Fallback to recovery ROM
            url = self._get_latest_recovery_url(codename)

        if not url:
            logger.error(f"No firmware found for codename: {codename}")
            return None

        filename = url.split("/")[-1]
        output_path = self._download_dir / "xiaomi" / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Downloading Xiaomi firmware: {filename}")
        try:
            resp = self._session.get(url, stream=True, timeout=600)
            resp.raise_for_status()

            total = int(resp.headers.get("content-length", 0))
            downloaded = 0

            with open(output_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total > 0:
                        progress_callback(downloaded, total)

            return str(output_path)
        except requests.RequestException as e:
            logger.error(f"Xiaomi firmware download failed: {e}")
            return None

    def search(self, model: str, manufacturer: str = "xiaomi") -> Optional[Dict]:
        """Search for available Xiaomi firmware."""
        codename = self._model_to_codename(model)
        if not codename:
            return None

        url = self._get_latest_fastboot_url(codename)
        if url:
            return {
                "source": self.name,
                "model": model,
                "codename": codename,
                "filename": url.split("/")[-1],
                "url": url,
                "type": "fastboot",
            }
        return None

    def set_download_dir(self, path: Path) -> None:
        self._download_dir = path

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _get_latest_fastboot_url(self, codename: str) -> Optional[str]:
        """Get latest fastboot ROM URL for a codename."""
        devices_url = (
            f"{self.API_BASE}/xiaomifirmwareupdater.github.io/master/"
            f"data/devices/{codename}.yml"
        )
        try:
            resp = self._session.get(devices_url, timeout=15)
            if resp.status_code != 200:
                return None
            # Parse YAML-like response for fastboot link
            for line in resp.text.split("\n"):
                if "fastboot:" in line:
                    return line.split(":", 1)[1].strip()
        except requests.RequestException:
            pass
        return None

    def _get_latest_recovery_url(self, codename: str) -> Optional[str]:
        """Get latest recovery ROM URL."""
        devices_url = (
            f"{self.API_BASE}/xiaomifirmwareupdater.github.io/master/"
            f"data/devices/{codename}.yml"
        )
        try:
            resp = self._session.get(devices_url, timeout=15)
            if resp.status_code != 200:
                return None
            for line in resp.text.split("\n"):
                if "recovery:" in line:
                    return line.split(":", 1)[1].strip()
        except requests.RequestException:
            pass
        return None

    @staticmethod
    def _model_to_codename(model: str) -> Optional[str]:
        """
        Map Xiaomi model number to codename.
        This database should be updated regularly.
        """
        # Common Xiaomi model -> codename mappings
        mappings = {
            "23021RAAEG": "topaz",      # Redmi Note 12 4G
            "2304FPN6DG": "sweet_k6a",  # Redmi Note 12 Pro 4G
            "2201116SG": "veux",        # Redmi Note 11 Pro 5G
            "2203129G": "lisa",         # Xiaomi 11 Lite 5G NE
            "2210132G": "munch",        # POCO F4
            "21091116AG": "pissarro",   # Redmi Note 11 Pro
            "2201117TG": "fog",         # Redmi 10C
            "M2012K11AG": "alioth",     # POCO F3
            "M2007J20CG": "apollo",     # Mi 10T
        }
        return mappings.get(model)
