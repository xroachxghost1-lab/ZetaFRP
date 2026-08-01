# Zeta FRP Wizard — Method Catalog

## Complete FRP Bypass Method Reference (July 2026)

### Tier 1: Flashing-Based Methods (Most Reliable)

| Method | Brands | Risk | Requirements |
|--------|--------|------|--------------|
| Samsung Odin Combination Firmware | Samsung | High | Combination firmware, Odin3 |
| Qualcomm EDL 9008 Mode | Xiaomi, Oppo, OnePlus, Motorola | Critical | Firehose programmer |
| MediaTek SP Flash Tool | Xiaomi, Vivo, Realme, Tecno | Critical | Scatter file, VCOM drivers |
| Fastboot FRP Erase | Google Pixel, Motorola, OnePlus | High | Unlocked bootloader |

### Tier 2: ADB-Based Methods (Conditional)

| Method | SDK Range | Requirements |
|--------|-----------|--------------|
| user_setup_complete Bypass | 21+ | USB debugging pre-enabled |
| Samsung ADB Bypass | 21+ | USB debugging, Samsung-specific commands |

### Tier 3: Interactive Exploits (Mostly Patched)

| Method | Patched After SPL | Target Devices |
|--------|-------------------|----------------|
| TalkBack Accessibility | March 2024 | Samsung Android 12-13 |
| Emergency Dialer | June 2024 | Samsung, LG, Motorola |
| Keyboard Settings Hijack | March 2024 | Various Android 9-12 |
| Chrome APK Download | Blocked by Google 2025 | All brands (patched) |

### Tier 4: CVE-Based Exploits (Patched)

| CVE | Description | Patched |
|-----|-------------|---------|
| CVE-2025-22414 | FRP Alert Activity priv esc | March 2025 |
| CVE-2024-53150 | Kernel vulnerability | April 2025 |
| CVE-2024-53197 | Kernel vulnerability | April 2025 |

## SPL Compatibility Matrix

```

SPL Date      │ Interactive │ ADB     │ CVE     │ Flashing
──────────────┼─────────────┼─────────┼─────────┼─────────
Before Mar 2024 │     ✅      │   ✅    │   ✅    │   ✅
Mar-Jun 2024    │     ❌      │   ✅    │   ✅    │   ✅
Jun 2024-Mar 2025│    ❌      │   ✅    │   ✅    │   ✅
After Mar 2025  │     ❌      │   ✅*   │   ❌    │   ✅
After Apr 2025  │     ❌      │   ✅*   │   ❌    │   ✅

- Requires pre-enabled USB debugging

```

