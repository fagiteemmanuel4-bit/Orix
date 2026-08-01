# Changelog

All notable changes to Orix X will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] - 2025-02-15

### Added
- **Plugin-based architecture** featuring a decoupled core engine.
- Dynamic auto-discovery of framework plugins in `orix/plugins/`.
- Dynamic template rendering recursively via Jinja2 engine, including path naming interpolation.
- Deterministic CLI option support matching interactive forms (`--framework`, `--docker`, `--auth`).
- Interactive TUI utilizing `rich` and `questionary`.
- Full pytest test suite covering core operations, rendering, and plugin loading.
- High-quality open-source governance guidelines, code of conduct, and templates.

### Removed
- Legacy manual virtual environment directories and zip artifacts from the root directory to optimize repo health.
- Duplicate or hardcoded template configurations.
