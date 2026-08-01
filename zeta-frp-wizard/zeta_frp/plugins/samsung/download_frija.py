#!/usr/bin/env python3
"""
Zeta FRP Wizard — Samsung Firmware Downloader (Frija API)
===========================================================
Downloads Samsung stock/combination firmware from Samsung Kies
servers using the Frija API protocol.

Reference: https://github.com/ysfchn/SamFetch
           https://xdaforums.com/t/tool-frija-samsung-firmware-downloader-checker.3910594/

ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
Unauthorised use, distribution, or reproduction is an act of war.
Copyright © 2026 Zeta Omniverse. All rights reserved.
"""

import requests
import json
import os
import hashlib
from pathlib import Path
from typing import Optional, Dict, Tuple
from dataclasses import dataclass

from zeta_frp.utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class FirmwareInfo:
    """Information about a firmware binary."""
    model: str
    csc: str
    version: str
    android_version: str
    size_bytes: int
    filename: str
    download_url: str
    md5: str = ""

class SamsungFirmwareDownloader:
    """
    Downloads Samsung firmware from Kies/FUS servers.

    Samsung's Kies/FUS (Firmware Update Server) API is used by
    Frija and SamFirm to download official firmware binaries.

    NOTE: As of 2025, Samsung requires IMEI validation for
    firmware downloads. The IMEI must match the requested model.
    """

    FUS_BASE_URL = "https://fota-cloud-dn.ospserver.net/firmware"
    FUS_SERVICE_URL = "https://fota.ospserver.net"

    def __init__(self, download_dir: Optional[str] = None):
        if download_dir:
            self._download_dir = Path(download_dir)
        else:
            self._download_dir = Path.home() / "ZetaFRP" / "firmware" / "samsung"
        self._download_dir.mkdir(parents=True, exist_ok=True)
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "Kies2.0_FUS",
            "Content-Type": "application/x-www-form-urlencoded",
        })

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search_firmware(self, model: str, csc: str = "AUTO",
                        imei: Optional[str] = None) -> Optional[FirmwareInfo]:
        """
        Search for the latest firmware for a Samsung device.

        Args:
            model: Device model (e.g., SM-G991B)
            csc: CSC/region code (e.g., XEU, BTU). Use 'AUTO' for automatic.
            imei: Device IMEI for Samsung's new validation requirement.

        Returns:
            FirmwareInfo if found, None otherwise.
        """
        if csc == "AUTO":
            csc = self._detect_csc(model, imei)

        logger.info(f"Searching firmware for {model} (CSC: {csc})...")

        # Build FUS request
        fus_request = self._build_fus_request(model, csc, imei)

        try:
            resp = self._session.post(
                f"{self.FUS_BASE_URL}/{csc}/{model}/version.xml",
                data=fus_request,
                timeout=30,
            )
            if resp.status_code != 200:
                logger.error(f"FUS returned HTTP {resp.status_code}")
                return None

            info = self._parse_fus_response(resp.text, model, csc)
            if info:
                logger.info(f"Found firmware: {info.version} ({info.size_bytes} bytes)")
            return info

        except requests.RequestException as e:
            logger.error(f"FUS request failed: {e}")
            return None

    def download_firmware(self, info: FirmwareInfo,
                          progress_callback=None) -> Optional[str]:
        """
        Download a firmware binary.

        Args:
            info: FirmwareInfo from search_firmware().
            progress_callback: Optional callable(bytes_downloaded, total_bytes).

        Returns:
            Path to downloaded file, or None if download failed.
        """
        output_path = self._download_dir / info.filename

        if output_path.exists():
            # Verify existing file
            if info.md5 and self._verify_md5(str(output_path), info.md5):
                logger.info(f"Firmware already downloaded and verified: {output_path}")
                return str(output_path)
            logger.warning(f"Existing file failed MD5 check. Re-downloading...")

        logger.info(f"Downloading {info.filename} ({info.size_bytes / 1e6:.0f} MB)...")

        try:
            resp = self._session.get(info.download_url, stream=True, timeout=600)
            resp.raise_for_status()

            total = int(resp.headers.get("content-length", 0))
            downloaded = 0

            with open(output_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total > 0:
                        progress_callback(downloaded, total)

            # Verify download
            if info.md5 and not self._verify_md5(str(output_path), info.md5):
                logger.error("Downloaded file failed MD5 verification")
                output_path.unlink()
                return None

            logger.info(f"Firmware downloaded: {output_path}")
            return str(output_path)

        except requests.RequestException as e:
            logger.error(f"Download failed: {e}")
            if output_path.exists():
                output_path.unlink()
            return None

    def get_combination_firmware(self, model: str,
                                  binary_version: str = "") -> Optional[FirmwareInfo]:
        """
        Search for combination (factory) firmware.
        Combination firmware enables ADB and is used for FRP bypass.
        """
        # Combination firmware is typically distributed via community sources,
        # not directly from Kies. This method searches community databases.
        logger.info(f"Searching combination firmware for {model}...")

        # Community firmware databases
        sources = [
            f"https://samfw.com/firmware/{model}",
            f"https://www.samfrew.com/model/{model}",
        ]

        for source in sources:
            try:
                resp = self._session.get(source, timeout=15)
                if resp.status_code == 200 and "COMBINATION" in resp.text.upper():
                    logger.info(f"Combination firmware found at {source}")
                    # Extract firmware info from page
                    return self._parse_community_page(resp.text, model)
            except requests.RequestException:
                continue

        logger.warning(f"No combination firmware found for {model}")
        return None

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _build_fus_request(self, model: str, csc: str,
                           imei: Optional[str] = None) -> str:
        """Build the XML request body for Samsung FUS."""
        imei_xml = f"<IMEI>{imei}</IMEI>" if imei else ""
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<FUSMsg>'
            '<FUSHdr>'
            '<ProtoVer>1.0</ProtoVer>'
            '<SessionID>0</SessionID>'
            '<MsgID>1</MsgID>'
            '</FUSHdr>'
            '<FUSBody>'
            '<Put>'
            f'<ACCESS_MODE><Data>2</Data></ACCESS_MODE>'
            f'<BINARY_NATURE><Data>1</Data></BINARY_NATURE>'
            f'<CLIENT_PRODUCT><Data>Smart Switch</Data></CLIENT_PRODUCT>'
            f'<DEVICE_FW_VERSION><Data></Data></DEVICE_FW_VERSION>'
            f'<DEVICE_LOCAL_CODE><Data>{csc}</Data></DEVICE_LOCAL_CODE>'
            f'<DEVICE_MODEL_NAME><Data>{model}</Data></DEVICE_MODEL_NAME>'
            f'<LOGIC_CHECK><Data>0</Data></LOGIC_CHECK>'
            f'{imei_xml}'
            '</Put>'
            '</FUSBody>'
            '</FUSMsg>'
        )

    def _parse_fus_response(self, xml_text: str, model: str,
                            csc: str) -> Optional[FirmwareInfo]:
        """Parse Samsung FUS XML response."""
        import xml.etree.ElementTree as ET

        try:
            root = ET.fromstring(xml_text)
            ns = {"ns": "http://www.w3.org/2001/XMLSchema-instance"}

            version = self._get_xml_value(root, "CURRENT_OS_VERSION") or \
                      self._get_xml_value(root, "LATEST_FW_VERSION") or "Unknown"
            filename = self._get_xml_value(root, "BINARY_NAME") or \
                       f"{model}_{version}.tar.md5"
            download_url = self._get_xml_value(root, "BINARY_URI") or \
                           self._get_xml_value(root, "MODEL_PATH") or ""
            size_str = self._get_xml_value(root, "BINARY_BYTE") or "0"
            md5 = self._get_xml_value(root, "BINARY_MD5") or ""

            return FirmwareInfo(
                model=model,
                csc=csc,
                version=version,
                android_version=version.split(".")[0] if version else "Unknown",
                size_bytes=int(size_str),
                filename=filename,
                download_url=download_url,
                md5=md5,
            )
        except ET.ParseError as e:
            logger.error(f"Failed to parse FUS response: {e}")
            return None

    def _parse_community_page(self, html: str, model: str) -> Optional[FirmwareInfo]:
        """Parse a community firmware page for combination firmware info."""
        # Basic scraping — community pages vary in structure
        import re

        url_match = re.search(r'href="([^"]*COMBINATION[^"]*\.(?:tar|zip|md5))"', html, re.I)
        if url_match:
            return FirmwareInfo(
                model=model,
                csc="FACTORY",
                version="COMBINATION",
                android_version="Factory",
                size_bytes=0,
                filename=url_match.group(1).split("/")[-1],
                download_url=url_match.group(1),
            )
        return None

    @staticmethod
    def _get_xml_value(element, tag: str) -> Optional[str]:
        """Extract text value from XML Data element."""
        for elem in element.iter():
            if elem.tag == tag:
                data = elem.find("Data")
                if data is not None and data.text:
                    return data.text
        return None

    @staticmethod
    def _detect_csc(model: str, imei: Optional[str] = None) -> str:
        """Attempt to detect CSC from model or IMEI."""
        # Common CSC codes by model prefix
        csc_map = {
            "SM-G99": "XEU",    # European Galaxy S21 series
            "SM-S90": "XEU",    # European Galaxy S22 series
            "SM-S91": "XEU",    # European Galaxy S23 series
            "SM-S92": "XEU",    # European Galaxy S24 series
            "SM-A": "XEU",      # European Galaxy A series
            "SM-F": "XEU",      # European Galaxy Z Fold/Flip
            "SM-N": "XEU",      # European Galaxy Note
            "SM-T": "XEU",      # European Galaxy Tab
        }
        for prefix, csc in csc_map.items():
            if model.upper().startswith(prefix):
                return csc
        return "XEU"  # Default to European

    @staticmethod
    def _verify_md5(filepath: str, expected_md5: str) -> bool:
        """Verify MD5 checksum of a file."""
        if not expected_md5:
            return True
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest().lower() == expected_md5.lower()
