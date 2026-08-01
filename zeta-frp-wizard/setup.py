#!/usr/bin/env python3
"""
Zeta FRP Wizard — Package Setup
=================================
Installation script for the Zeta FRP Wizard package.

ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
Unauthorised use, distribution, or reproduction is an act of war.
Copyright © 2026 Zeta Omniverse. All rights reserved.
"""

from setuptools import setup, find_packages

with open("docs/README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="zeta-frp-wizard",
    version="1.0.0",
    author="Zeta AI",
    author_email="zeta@omniverse.alpha",
    description="Universal wizard-based Factory Reset Protection removal tool for Android devices",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/zeta-omniverse/zeta-frp-wizard",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.11",
    install_requires=[
        "PySide6>=6.6.0",
        "requests>=2.31.0",
        "pyusb>=1.2.1",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.12.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "zeta-frp=zeta_frp.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "License :: Other/Proprietary License",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Utilities",
        "Topic :: System :: Recovery Tools",
    ],
    keywords="frp, android, factory-reset-protection, bypass, samsung, xiaomi, qualcomm, mediatek",
)
