# Zeta FRP Wizard — Architecture Document

## System Overview

The Zeta FRP Wizard is a modular desktop application built on Python and PySide6,
designed to remove Factory Reset Protection from Android devices.

## Component Diagram

```

┌─────────────────────────────────────────────┐
│              GUI Layer (PySide6)              │
│  ┌─────────┐ ┌──────────┐ ┌───────────────┐ │
│  │ Welcome  │ │  Detect  │ │ Method Select │ │
│  └─────────┘ └──────────┘ └───────────────┘ │
│  ┌─────────┐ ┌──────────┐ ┌───────────────┐ │
│  │Firmware │ │ Execute  │ │  Verification │ │
│  └─────────┘ └──────────┘ └───────────────┘ │
└──────────────────┬──────────────────────────┘
│
┌──────────────────▼──────────────────────────┐
│            Core Engine Layer                  │
│  ┌────────────────┐ ┌────────────────────┐   │
│  │ Device Detector │ │  Method Engine      │   │
│  │  - ADB scanner  │ │  - SPL Checker      │   │
│  │  - Fastboot     │ │  - Method Selector  │   │
│  │  - EDL/BROM     │ │  - Plan Builder     │   │
│  └────────────────┘ └────────────────────┘   │
└──────────────────┬──────────────────────────┘
│
┌──────────────────▼──────────────────────────┐
│              Plugin Layer                     │
│  ┌──────┐ ┌───────┐ ┌───────┐ ┌──────────┐  │
│  │Samsung│ │Qualcomm│ │Mediatek│ │Universal │  │
│  │ Odin  │ │  EDL   │ │SP Flash│ │   ADB    │  │
│  └──────┘ └───────┘ └───────┘ └──────────┘  │
└──────────────────┬──────────────────────────┘
│
┌──────────────────▼──────────────────────────┐
│           Infrastructure Layer                │
│  ┌────────┐ ┌──────────┐ ┌───────────────┐  │
│  │  ADB   │ │ Fastboot  │ │   Firmware    │  │
│  │Wrapper │ │  Wrapper  │ │  Downloader   │  │
│  └────────┘ └──────────┘ └───────────────┘  │
└─────────────────────────────────────────────┘

```

## Key Design Patterns

### Strategy Pattern (Method Engine)
The Method Engine uses Strategy pattern to select and execute the optimal bypass method based on device properties and Security Patch Level.

### Plugin Architecture
Each brand/SoC combination is implemented as a plugin inheriting from `FRPBypassPlugin`. Plugins are auto-discovered and loaded at runtime.

### Observer Pattern (GUI Signals)
PySide6 signals connect the core engine to the GUI, enabling real-time progress updates and log streaming.

## Data Flow

1. Device Detection → DetectedDevice object
2. SPL Checker → Method availability assessment
3. Method Engine → ExecutionPlan with ordered steps
4. Plugin → Brand-specific bypass execution
5. Verification → Success/failure report
