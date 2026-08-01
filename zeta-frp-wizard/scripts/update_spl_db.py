#!/usr/bin/env python3
"""
Zeta FRP Wizard — SPL Database Updater
=========================================
Validates and updates the Security Patch Level
to method mapping database.

ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
Unauthorised use, distribution, or reproduction is an act of war.
Copyright © 2026 Zeta Omniverse. All rights reserved.
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from zeta_frp.core.spl_checker import SPLChecker, MethodAvailability
from zeta_frp.utils.logger import setup_logging, get_logger

logger = get_logger(__name__)

def validate_methods():
    """Validate all methods in the SPL database."""
    checker = SPLChecker()
    methods = checker.METHOD_DB

    logger.info(f"Validating {len(methods)} methods in SPL database...")

    errors = []
    warnings = []

    for method in methods:
        # Check required fields
        if not method.name:
            errors.append(f"Method {method.category} has no name")
        if method.min_sdk < 21:
            warnings.append(f"{method.name}: min_sdk {method.min_sdk} is below Android 5.1")
        if method.max_sdk > 0 and method.max_sdk < method.min_sdk:
            errors.append(f"{method.name}: max_sdk < min_sdk")
        if method.risk_level not in ("low", "medium", "high", "critical"):
            errors.append(f"{method.name}: invalid risk_level '{method.risk_level}'")

    if errors:
        logger.error(f"Found {len(errors)} errors:")
        for e in errors:
            logger.error(f"  - {e}")
        return False

    if warnings:
        logger.warning(f"Found {len(warnings)} warnings:")
        for w in warnings:
            logger.warning(f"  - {w}")

    logger.info("SPL database validation complete — all methods OK")
    return True

def show_method_coverage():
    """Display method coverage across brands and SDK levels."""
    checker = SPLChecker()
    methods = checker.METHOD_DB

    brands = set()
    for m in methods:
        for b in m.brands:
            brands.add(b)

    print("\n=== Method Coverage Report ===")
    print(f"Total methods: {len(methods)}")
    print(f"Covered brands: {', '.join(sorted(brands)) if brands else 'ALL'}")
    print()

    for method in methods:
        sdk_range = f"SDK {method.min_sdk}"
        if method.max_sdk > 0:
            sdk_range += f"-{method.max_sdk}"
        else:
            sdk_range += "+"

        spl_info = "No SPL patch" if method.patched_after_spl is None \
                   else f"Patched after {method.patched_after_spl}"

        print(f"  {method.name}")
        print(f"    SDK: {sdk_range} | Risk: {method.risk_level} | {spl_info}")
        if method.brands:
            print(f"    Brands: {', '.join(method.brands)}")
        print()

if __name__ == "__main__":
    setup_logging(level="INFO")
    if validate_methods():
        show_method_coverage()
    else:
        sys.exit(1)
