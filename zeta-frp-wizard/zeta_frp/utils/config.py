#!/usr/bin/env python3
"""
Zeta FRP Wizard — Configuration Manager
=========================================
JSON-based configuration with environment variable overrides
and automatic migration. Thread-safe reads, batched writes.

ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
Unauthorised use, distribution, or reproduction is an act of war.
Copyright © 2026 Zeta Omniverse. All rights reserved.
"""

import json
import os
import threading
from pathlib import Path
from typing import Any, Dict, Optional

from zeta_frp.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_CONFIG: Dict[str, Any] = {
    "general": {
        "language": "en",
        "theme": "dark",
        "check_updates": True,
        "update_channel": "stable",
    },
    "adb": {
        "path": "",
        "port": 5037,
        "timeout": 15,
    },
    "firmware": {
        "download_dir": "",
        "verify_checksums": True,
        "max_concurrent_downloads": 2,
    },
    "flashing": {
        "verify_before_flash": True,
        "backup_persist": False,
        "auto_reboot": True,
    },
    "advanced": {
        "debug_mode": False,
        "developer_options": False,
        "custom_firehose_dir": "",
    },
}

class ConfigManager:
    """
    Singleton-style configuration manager.

    Usage:
        cfg = ConfigManager()
        cfg.load()
        adb_path = cfg.get("adb.path")
        cfg.set("adb.timeout", 30)
        cfg.save()
    """

    _instance: Optional["ConfigManager"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "ConfigManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._data = DEFAULT_CONFIG.copy()
                    cls._instance._loaded = False
                    cls._instance._config_path = cls._get_config_path()
        return cls._instance

    @staticmethod
    def _get_config_path() -> Path:
        """Determine the config file location based on platform."""
        if os.name == "nt":
            base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        elif sys.platform.startswith("darwin"):
            base = Path.home() / "Library" / "Application Support"
        else:
            base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        return base / "ZetaFRP" / "config.json"

    def load(self, path: Optional[Path] = None) -> None:
        """
        Load configuration from disk. Merges with defaults so new keys
        are always available even if config file is from an older version.
        """
        if path:
            self._config_path = path

        if self._config_path.exists():
            try:
                with open(self._config_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                # Deep merge loaded into defaults
                self._deep_merge(self._data, loaded)
                self._loaded = True
                logger.info(f"Configuration loaded from {self._config_path}")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load config: {e}. Using defaults.")
        else:
            logger.info("No config file found. Using defaults.")
            self._loaded = True

    def save(self) -> None:
        """Persist current configuration to disk."""
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Configuration saved to {self._config_path}")
        except IOError as e:
            logger.error(f"Failed to save config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot-notation.

        Args:
            key: Dot-separated path, e.g. "adb.timeout"
            default: Fallback value if key not found.

        Returns:
            The configuration value or default.
        """
        env_key = f"ZETA_FRP_{key.upper().replace('.', '_')}"
        env_val = os.environ.get(env_key)
        if env_val is not None:
            # Cast to appropriate type based on default
            if isinstance(default, bool):
                return env_val.lower() in ("1", "true", "yes")
            if isinstance(default, int):
                return int(env_val)
            return env_val

        parts = key.split(".")
        node = self._data
        for part in parts:
            if isinstance(node, dict) and part in node:
                node = node[part]
            else:
                return default
        return node

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value using dot-notation.

        Args:
            key: Dot-separated path.
            value: Value to store.
        """
        parts = key.split(".")
        node = self._data
        for part in parts[:-1]:
            if part not in node:
                node[part] = {}
            node = node[part]
        node[parts[-1]] = value

    def reset(self, section: Optional[str] = None) -> None:
        """
        Reset configuration to defaults.

        Args:
            section: If provided, reset only that section.
        """
        if section and section in DEFAULT_CONFIG:
            self._data[section] = DEFAULT_CONFIG[section].copy()
        else:
            self._data = DEFAULT_CONFIG.copy()

    @staticmethod
    def _deep_merge(base: dict, override: dict) -> None:
        """Recursively merge override dict into base dict in-place."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                ConfigManager._deep_merge(base[key], value)
            else:
                base[key] = value
