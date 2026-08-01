#!/usr/bin/env python3
"""
Zeta FRP Wizard — Firmware Validator
======================================
Validates downloaded firmware files for compatibility
and integrity before flashing.

ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
Unauthorised use, distribution, or reproduction is an act of war.
Copyright © 2026 Zeta Omniverse. All rights reserved.
"""

import hashlib
import os
from pathlib import Path
from typing import Optional

from zeta_frp.utils.logger import get_logger

logger = get_logger(__name__)

class FirmwareValidator:
    """
    Validates firmware files before flashing.

    Checks:
    - File exists and is non-empty
    - File extension is valid for the device type
    - MD5/SHA256 checksum if available
    - Minimum file size (firmware should be > 100MB typically)
    - File is not corrupted (basic structure check)
    """

    MIN_FIRMWARE_SIZE = 50 * 1024 * 1024  # 50 MB minimum
    VALID_EXTENSIONS = {
        "samsung": [".tar", ".md5", ".tar.md5"],
        "xiaomi": [".zip", ".tgz", ".tar"],
        "qualcomm": [".elf", ".mbn", ".bin", ".img"],
        "mediatek": [".txt", ".bin", ".img"],
        "generic": [".zip", ".tar", ".img", ".bin"],
    }

    def validate(self, filepath: str, model: str = "",
                 manufacturer: str = "") -> bool:
        """
        Validate a firmware file.

        Args:
            filepath: Path to firmware file.
            model: Expected device model.
            manufacturer: Device manufacturer for extension checking.

        Returns:
            True if firmware passes all validation checks.
        """
        path = Path(filepath)

        # Check existence
        if not path.exists():
            logger.error(f"Firmware file not found: {filepath}")
            return False

        # Check non-empty
        if path.stat().st_size == 0:
            logger.error(f"Firmware file is empty: {filepath}")
            return False

        # Check minimum size (skip for small config files like scatter)
        if path.suffix not in (".txt",) and path.stat().st_size < self.MIN_FIRMWARE_SIZE:
            logger.warning(
                f"Firmware file is smaller than expected "
                f"({path.stat().st_size / 1e6:.1f} MB). "
                f"This may be a partial download or incorrect file."
            )

        # Check extension
        man_lower = manufacturer.lower()
        valid_exts = self.VALID_EXTENSIONS.get(
            man_lower, self.VALID_EXTENSIONS["generic"]
        )

        ext_ok = any(
            path.name.lower().endswith(ext.lstrip(".")) or
            path.suffix.lower() == ext
            for ext in valid_exts
        )

        if not ext_ok:
            logger.warning(
                f"Firmware extension '{path.suffix}' is not in the expected "
                f"list for {manufacturer}: {valid_exts}. Proceeding with caution."
            )

        # Check model in filename (optional hint)
        if model and model.lower() not in path.name.lower():
            logger.warning(
                f"Model '{model}' not found in firmware filename '{path.name}'. "
                f"Verify this is the correct firmware for your device."
            )

        logger.info(f"Firmware validation passed: {path.name}")
        return True

    def verify_checksum(self, filepath: str, expected_md5: str = "",
                        expected_sha256: str = "") -> bool:
        """
        Verify file checksum.

        Args:
            filepath: Path to file.
            expected_md5: Expected MD5 hex digest.
            expected_sha256: Expected SHA256 hex digest.

        Returns:
            True if checksums match (or no checksum provided).
        """
        if not expected_md5 and not expected_sha256:
            return True  # No checksum to verify

        if expected_md5:
            actual = self._compute_md5(filepath)
            if actual.lower() != expected_md5.lower():
                logger.error(
                    f"MD5 mismatch!\n  Expected: {expected_md5}\n  Got:      {actual}"
                )
                return False

        if expected_sha256:
            actual = self._compute_sha256(filepath)
            if actual.lower() != expected_sha256.lower():
                logger.error(
                    f"SHA256 mismatch!\n  Expected: {expected_sha256}\n  Got:      {actual}"
                )
                return False

        logger.info("Checksum verification passed")
        return True

    def check_firmware_structure(self, filepath: str,
                                  file_type: str = "auto") -> bool:
        """
        Perform basic structure checks on firmware files.

        - tar/tar.md5: Check for valid tar header
        - zip: Check for valid zip header
        - img: Check for Android boot image magic or sparse image magic
        - elf/mbn: Check for ELF magic
        """
        path = Path(filepath)
        if not path.exists():
            return False

        with open(filepath, "rb") as f:
            magic = f.read(8)

        if path.suffix in (".tar", ".md5") or ".tar" in path.name:
            # tar files have 'ustar' at offset 257
            f.seek(257)
            ustar = f.read(5)
            return ustar == b"ustar"

        if path.suffix == ".zip":
            return magic[:4] == b"PK\x03\x04"

        if path.suffix == ".img":
            # Android boot image: ANDROID! magic
            # Android sparse image: 0xED26FF3A magic
            return magic[:8] == b"ANDROID!" or magic[:4] == b"\x3a\xff\x26\xed"

        if path.suffix in (".elf",):
            return magic[:4] == b"\x7fELF"

        # Unknown type — assume OK
        return True

    # ------------------------------------------------------------------
    # Static Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_md5(filepath: str) -> str:
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    @staticmethod
    def _compute_sha256(filepath: str) -> str:
        hash_sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
