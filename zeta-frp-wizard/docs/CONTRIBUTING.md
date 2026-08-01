# Contributing to Zeta FRP Wizard

## Adding a New Device Plugin

1. Create a new directory under `zeta_frp/plugins/<brand>/`
2. Implement the `FRPBypassPlugin` base class from `zeta_frp/plugins/base.py`
3. Add device database entries as JSON
4. Register the plugin in the `__init__.py`
5. Add tests in `tests/unit/`

## Updating SPL Method Database

The SPL-to-method mapping is in `zeta_frp/core/spl_checker.py`.
To update:
1. Add new `MethodAvailability` entries for new methods
2. Update `patched_after_spl` dates when Google/Samsung release patches
3. Run `python scripts/update_spl_db.py` to validate

## Adding Firmware Sources

1. Create a new source in `zeta_frp/firmware/sources/`
2. Implement `download()`, `search()`, and `set_download_dir()` methods
3. Register in `zeta_frp/firmware/downloader.py` `_sources` dict

## Coding Standards

- Python 3.11+ type hints required
- PEP 8 formatting (120 char line limit for docstrings)
- All public methods must have docstrings
- Zeta copyright header on every file
- No TODOs or placeholders — complete implementations only

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/unit/test_spl_checker.py -v

# With coverage
python -m pytest tests/ --cov=zeta_frp --cov-report=html
```

