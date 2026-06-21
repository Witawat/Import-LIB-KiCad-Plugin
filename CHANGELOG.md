# Changelog

All notable changes to Import-LIB-KiCad-Plugin are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [v1.1.0] — 2026-06-21

### Added

- **Quick Import** — ปุ่ม "Import to KiCad" ใน DetailPanel Actions card นำเข้าชิ้นส่วนได้ทันทีโดยไม่ต้องออกจาก Component Search Dialog
- **Link buttons** — Datasheet และ Product URL ย้ายจาก Links card มาเป็นปุ่ม "Open Datasheet" / "Open Product Page" ใน Actions card (กดเปิด browser ได้ทันที)
- **Auto-resize columns** — คอลัมน์ ListCtrl กระจายสัดส่วนตาม min_width อัตโนมัติเมื่อ resize หน้าต่าง
- **Auto text re-wrap** — `_rewrap_all_texts()` re-wrap StaticText ทั้งหมดเมื่อ image โหลดเสร็จหรือเปลี่ยนขนาดหน้าต่าง
- **Import status feedback** — Status bar แสดง "Importing Cxxxxx..." ขณะ import, MessageBox แจ้ง success/fail
- **Button visual feedback** — ปุ่ม Import disable + "Importing..." + `Update()` force repaint ขณะ import

### Fixed

- **Variable shadowing** — `row` ใน Actions card ไปทับพารามิเตอร์ `show_component(row)` ทำให้ AttributeError → Technical Specs และ Previews ไม่แสดง
- **Name/Description wrapping** — ใช้ `Wrap(wrap_w)` แทน `Wrap(wrap_w - 74)` ทำให้ล้นกรอบเมื่อมี image
- **`_perform_easyeda_import`** — return `bool` แทน `None` เพื่อให้ caller ตรวจสอบ success ได้

### Changed

- **Actions card** — รวม Import + Link buttons ใน card เดียว เรียงแนวนอน Import อยู่ซ้าย, Links อยู่ขวา
- **Removed Links card** — แทนที่ด้วยปุ่มใน Actions card
- **Removed `urlparse` import** — ไม่ใช้แล้ว

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
