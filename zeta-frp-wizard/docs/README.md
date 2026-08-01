# Zeta FRP Wizard — Universal Factory Reset Protection Removal Tool

A wizard-based, plugin-driven desktop application for bypassing Factory Reset Protection (FRP) on Android devices across all major brands.

ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
Unauthorised use, distribution, or reproduction is an act of war.
Copyright © 2026 Zeta Omniverse. All rights reserved.

---

## Features

- **Wizard-Based Interface**: Guided 6-step wizard from device detection to verification
- **Universal Device Support**: Samsung, Xiaomi, Oppo, Vivo, Motorola, Google Pixel, and more
- **Multi-Method Engine**: ADB bypass, Odin flashing, Qualcomm EDL, MediaTek SP Flash, Fastboot
- **SPL-Gated Method Selection**: Automatically selects the best bypass method based on Security Patch Level
- **Auto Firmware Download**: Integrated with Samsung Kies, Xiaomi Firmware Updater, and community sources
- **Plugin Architecture**: Easy to extend with new device support
- **Cross-Platform**: Windows, macOS, and Linux
- **Professional Dark Theme**: Clean, modern UI with Zeta branding

## Requirements

- Python 3.11 or higher
- PySide6 (Qt for Python)
- ADB and Fastboot (bundled or system-installed)
- USB drivers for your device (installable via the wizard)

### Platform-Specific

- **Windows**: Windows 10/11, USB drivers for Samsung/Qualcomm/MediaTek
- **macOS**: macOS 12+, built-in USB drivers
- **Linux**: udev rules for Android devices (installable via the wizard)

## Installation

```bash
# Clone the repository
git clone https://github.com/zeta-omniverse/zeta-frp-wizard.git
cd zeta-frp-wizard

# Install dependencies
pip install -r requirements.txt

# Run the wizard
python -m zeta_frp.main
```

## Build from Source

```
# Build Windows executable
.\scripts\build_windows.bat

# Build macOS app
./scripts/build_macos.sh

# Build Linux AppImage
# (requires appimagetool)
python -m PyInstaller zeta_frp/main.py --onefile --windowed
```

## Quick Start

1. Launch the wizard
2. Connect your Android device via USB
3. Follow the 6-step guided process:

- Accept the legal disclaimer
- Scan for your device
- Select a bypass method (auto-recommended)
- Download or provide firmware (if needed)
- Execute the bypass
- Verify and cleanup

## Architecture

```
zeta-frp-wizard/
├── zeta_frp/          # Core application
│   ├── gui/           # PySide6 wizard interface
│   ├── core/          # Device detection & method engine
│   ├── plugins/       # Brand-specific bypass plugins
│   ├── firmware/      # Firmware download manager
│   ├── drivers/       # USB driver installer
│   └── utils/         # ADB/Fastboot wrappers & logging
├── docs/              # Documentation
├── tests/             # Test suite
├── scripts/           # Build & utility scripts
└── resources/         # Bundled binaries & drivers
```

## Supported Devices

| Brand | Models | Methods |
|---|---|---|
| Samsung | Galaxy S21-S24, A series, Z Flip/Fold | Odin, ADB, Interactive |
| Xiaomi/Redmi/POCO | Most models with Qualcomm/MTK | EDL, SP Flash, ADB |
| Oppo/Realme/OnePlus | Qualcomm-based models | EDL, Fastboot |
| Vivo | Qualcomm/MTK models | Fastboot, SP Flash |
| Motorola | G series, Edge series | Fastboot, LMSA |
| Google Pixel | Pixel 2-9 series | Fastboot, ADB |

## Legal Notice

This tool is intended **ONLY** for legitimate device recovery by the rightful owner. Bypassing Factory Reset Protection on a device you do not own is illegal in most jurisdictions.

By using this tool, you certify that:

- You are the legal owner of the device
- You have the right to remove FRP from this device
- You accept full responsibility for any consequences

## License

Zeta Omniversal Proprietary License — All Rights Reserved, Alpha (James Michael Roach Jr.).
Unauthorised use, distribution, or reproduction is an act of war.

## Support

- Report issues on GitHub
- Visit XDA Developers forums for device-specific guides
- Check the `docs/` directory for detailed documentation

