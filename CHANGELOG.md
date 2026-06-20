# Changelog

All notable changes to Import-LIB-KiCad-Plugin are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [v1.0.0] — 2026-06-20

### Added

- Component Search dialog — search JLCPCB / EasyEDA / LCSC parts in-app
- Real-time preview via `wx.html2.WebView` — EasyEDA viewer shows symbol and footprint
- Multi-format import: ZIP (Octopart, Samacsys, UltraLibrarian, Snapeda), EasyEDA, LCSC
- Library Browser — browse imported KiCad libraries
- Card-based DetailPanel layout with Basic Info, Stock & Pricing, Specs, Links, Previews
- `debug_log` toggle in `config.ini`
- Standalone EXE build (PyInstaller) — no KiCad or Python required
- GUI mode that runs without opening KiCad

### Fixed

- WebView Preview blank in PyInstaller build — `WebView2Loader.dll` now bundled via `--add-binary`; Edge WebView2 backend no longer falls back to IE
- `component_search.py` — `_create_webview()` explicitly requests Edge backend first; `_on_webview_error()` handler for diagnostics
- kiutils encoding issue in EXE build
- Config persistence fixes

### Changed

- DetailPanel redesigned from flat layout to card-based sections
- Replaced SVG renderer with `wx.html2.WebView` for component previews
- Improved image caching (LRU, max 50 entries)
- Filter dialog with brand/package/type exclusion and stock/price ranges
- Component Search dialog now opens at 85% screen width × 80% screen height
- Left result ListCtrl sash gravity set to 30% for proportional split

### Technical

- wxPython 4.2.2 + Python 3.11
- PyInstaller 6.21.0 — one-file windowed build
- EasyEDA API v2 integration via easyeda2kicad
