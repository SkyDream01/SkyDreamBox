# Repository Guidelines

## Project Structure & Module Organization

SkyDreamBox is a Python/PySide6 desktop GUI for FFmpeg workflows. Application entry and window wiring live in `main.py` and `ui_tabs.py`; shared behavior is split across `config.py`, `constants.py`, `process_handler.py`, `validators.py`, `utils.py`, `styles.py`, and `logger.py`. Generated Qt UI modules are under `ui/`, bundled icons under `assets/`, and tests under `tests/`. Runtime configuration is stored in `config/config.json` (or the user’s `%APPDATA%/SkyDreamBox/` fallback); do not commit local configuration or build output.

## Build, Test, and Development Commands

From the repository root:

```bash
pip install -r requirements.txt
python main.py
python -m unittest discover -s tests -v
python build.py
```

The first command installs PySide6; running the app requires `ffmpeg` and `ffprobe` on `PATH`. The test command runs the core and FFmpeg integration tests; FFmpeg-dependent cases are skipped when the executables are unavailable. `build.py` invokes Nuitka and packages the standalone Windows build, then uses 7-Zip for the self-extracting installer.

## Coding Style & Naming Conventions

Use Python 3.10+ conventions, four spaces per indentation level, and clear `snake_case` names for functions, methods, and variables. Use `PascalCase` for classes and `UPPER_SNAKE_CASE` for module constants. Keep Qt signal/slot handlers small, validate user input before constructing FFmpeg commands, and preserve existing path quoting and subprocess behavior. No formatter or linter is configured, so keep imports tidy and match surrounding style.

## Testing Guidelines

Tests use `unittest` and live in `tests/test_core.py`; test classes end in `Tests` and methods begin with `test_`. Set `QT_QPA_PLATFORM=offscreen` for headless runs (the suite does this automatically). Add regression coverage for validators, command construction, process failures, and GUI behavior affected by a change. There is currently no enforced coverage threshold.

## Commit & Pull Request Guidelines

Prefer concise Conventional Commit-style prefixes such as `feat:`, `fix:`, and `refactor:`; existing history also contains short Chinese descriptions, so language may follow the change context. Pull requests should explain the user-visible effect, list verification commands and external prerequisites, link an issue when applicable, and include screenshots or recordings for UI changes. Keep unrelated refactors out of focused changes.

## Security & Configuration Tips

Treat media paths and FFmpeg arguments as untrusted input. Do not commit credentials, personal config files, generated media, or `dist/` artifacts. Verify FFmpeg/FFprobe paths through the application settings or `PATH` before testing process changes.
