#!/usr/bin/env python3
"""
Zeta FRP Wizard — SPL Database Updater (improved)
- Adds CLI options: --check, --list, --fix, --dry-run, --verbose
- Safer imports, clearer logging, predictable exit codes
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
import logging

# ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

try:
    from zeta_frp.core.spl_checker import SPLChecker
    from zeta_frp.utils.logger import setup_logging, get_logger
except Exception as exc:
    print(f"Import error: {exc}", file=sys.stderr)
    raise

logger = logging.getLogger("update_spl_db")

def parse_args():
    p = argparse.ArgumentParser(description="Validate and update SPL method DB")
    p.add_argument("--list", action="store_true", help="List methods and basic metadata")
    p.add_argument("--check", action="store_true", help="Validate methods and exit with non-zero on error")
    p.add_argument("--fix", action="store_true", help="Attempt auto-fixes where safe (back up first)")
    p.add_argument("--dry-run", action="store_true", help="Show actions without making changes")
    p.add_argument("--verbose", "-v", action="count", default=0, help="Increase verbosity")
    return p.parse_args()

def report_methods(methods):
    for m in methods:
        brands = ", ".join(m.brands or [])
        max_sdk = m.max_sdk if m.max_sdk > 0 else "latest"
        print(f"{m.name} | cat={m.category} | SDK={m.min_sdk}-{max_sdk} | risk={m.risk_level} | brands={brands}")

def validate_methods(checker):
    methods = checker.METHOD_DB
    errors = []
    warnings = []
    for method in methods:
        if not getattr(method, "name", None):
            errors.append(f"Method {getattr(method, 'category', '<unknown>')} has no name")
        if getattr(method, "min_sdk", 0) < 21:
            warnings.append(f"{method.name}: min_sdk {method.min_sdk} is below Android 5.1")
        if getattr(method, "max_sdk", 0) > 0 and method.max_sdk < method.min_sdk:
            errors.append(f"{method.name}: max_sdk < min_sdk")
        if getattr(method, "risk_level", None) not in ("low", "medium", "high", "critical"):
            errors.append(f"{method.name}: invalid risk_level '{method.risk_level}'")
    return errors, warnings

def attempt_fix(methods, dry_run=False):
    backup = REPO_ROOT / "zeta-frp-wizard" / "spl_db_backup.json"
    logger.info("Creating backup of METHOD_DB (simulated) at: %s", backup)
    if dry_run:
        logger.info("[DRY RUN] Would create backup and apply fixes")
        return
    # Implementing real fixes depends on METHOD_DB format; this is a placeholder showing safe behavior.
    # For maintainers: add logic here to fix predictable issues (e.g. missing risk_level -> 'low')
    # and write back the DB, preserving formatting.
    logger.info("No automatic fixes implemented yet. Please implement domain fixes in tool if desired.")

def main():
    args = parse_args()
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(level=log_level)
    logger = get_logger(__name__)
    logger.info("Starting SPL DB updater (repo root: %s)", REPO_ROOT)

    checker = SPLChecker()
    methods = checker.METHOD_DB

    if args.list:
        report_methods(methods)
        return

    errors, warnings = validate_methods(checker)
    if warnings:
        logger.warning("Found %d warnings:", len(warnings))
        for w in warnings:
            logger.warning("  - %s", w)

    if errors:
        logger.error("Found %d errors:", len(errors))
        for e in errors:
            logger.error("  - %s", e)

    if args.check:
        if errors:
            logger.error("Validation failed")
            sys.exit(2)
        logger.info("Validation passed")
        sys.exit(0)

    if args.fix:
        attempt_fix(methods, dry_run=args.dry_run)

    if errors and not args.fix:
        logger.error("Errors detected; run with --fix to attempt automated fixes (if implemented) or inspect methods.")
        sys.exit(2)

    logger.info("SPL database validated.")
    if __name__ == "__main__":
        return

if __name__ == "__main__":
    main()
