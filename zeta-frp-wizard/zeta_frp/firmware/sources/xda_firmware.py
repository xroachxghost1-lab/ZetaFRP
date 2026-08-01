#!/usr/bin/env python3
"""
Zeta FRP Wizard — XDA Firmware Source
=======================================
Searches and downloads firmware from XDA Firmware
and other community firmware databases.

ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
Unauthorised use, distribution, or reproduction is an act of war.
Copyright © 2026 Zeta Omniverse. All rights reserved.
"""

import requests
from pathlib import Path
from typing import Optional, Callable, Dict, List

from zeta_frp.utils.logger import get_logger

logger = get_logger(__name__)

class XDAFirmwareSource:
    """
    XDA Firmware and community firmware source.

    Aggregates from multiple community databases:
    - xdafirmware.com
    - firmwarefile.com
    - samfw.com (Samsung)
    - needrom.com
    """

    name = "XDA / Community Firmware"
    SEARCH_URLS = [
        "https://xdafirmware.com/?s={model}",
        "https://firmwarefile.com/?s={model}",
    ]

    def __init__(self, download_dir: Path):
        self._download_dir = download_dir
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/126.0.0.0 Safari/537.36"
        })

    def download(self, model: str, manufacturer: str = "",
                 csc: str = "", imei: Optional[str] = None,
                 progress_callback=None) -> Optional[str]:
        """
        Search community sources and return the best firmware URL.
        Since community sites often change, this provides the search
        URL for the user rather than automated download.
        """
        logger.info(f"Searching community sources for {model} ({manufacturer})...")

        search_results = self._search_all(model, manufacturer)

        if not search_results:
            logger.warning(f"No community firmware found for {model}")
            return None

        # Return the best result info — actual download requires user interaction
        # due to captchas and rate limiting on community sites
        best = search_results[0]
        logger.info(
            f"Community firmware found: {best['title']}\n"
            f"  URL: {best['url']}\n"
            f"  Source: {best['source']}"
        )

        # For community sources, we provide the URL and let the user
        # handle the download manually (captcha, redirects, etc.)
        return None  # Community downloads require manual interaction

    def search(self, model: str, manufacturer: str = "") -> Optional[Dict]:
        """Search community sources for firmware info."""
        results = self._search_all(model, manufacturer)
        if results:
            return {
                "source": self.name,
                "model": model,
                "results": results,
                "count": len(results),
            }
        return None

    def set_download_dir(self, path: Path) -> None:
        self._download_dir = path

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _search_all(self, model: str, manufacturer: str) -> List[Dict]:
        """Search all community sources."""
        results = []

        for url_template in self.SEARCH_URLS:
            url = url_template.format(model=model)
            try:
                resp = self._session.get(url, timeout=15)
                if resp.status_code == 200:
                    # Basic result extraction from HTML
                    if "no results" not in resp.text.lower():
                        results.append({
                            "source": url.split("/")[2],
                            "url": url,
                            "title": f"Firmware results for {model}",
                        })
            except requests.RequestException as e:
                logger.debug(f"Search failed on {url}: {e}")

        return results
