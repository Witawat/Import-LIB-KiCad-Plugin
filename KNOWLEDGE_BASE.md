# KNOWLEDGE_BASE.MD — ความรู้โปรเจกต์ Import-LIB-KiCad-Plugin

## 基本信息

| รายการ | รายละเอียด |
|--------|------------|
| ผู้พัฒนา | Witawat (ต้นฉบับ: Steffen Wittemeier (Steffen-W)) |
| License | GPL-3.0 |
| KiCad ต่ำสุด | 8.0.4 |
| Python ต่ำสุด | 3.9 |
| OS | Windows, macOS, Linux |
| ประเภท | Action Plugin (pcbnew) |
| PCM ID | `com.github.Witawat.impartGUI` |

## ภาพรวมฟังก์ชันการทำงาน

Plugin นี้ใช้สำหรับ **นำเข้า Library ชิ้นส่วนอิเล็กทรอนิกส์** ที่ดาวน์โหลดจากเว็บต่าง ๆ เข้าสู่ KiCad โดยอัตโนมัติ:

1. **Octopart** — ZIP มี `device.lib` + `device.dcm` + `.pretty` folder
2. **Samacsys (Component Search Engine)** — ZIP มีโฟลเดอร์ `KiCad/`
3. **UltraLibrarian** — ZIP มีโฟลเดอร์ `KiCAD/` (สังเกตตัวพิมพ์ต่างกัน)
4. **SnapEDA** — ZIP มี structure แบน ๆ (.kicad_sym, .kicad_mod)
5. **EasyEDA / LCSC** — Import ผ่าน API (LCSC Part# เช่น C2040) ไม่ต้องใช้ ZIP

สิ่งที่ import ได้:
- Symbol library (`.kicad_sym`) — พร้อมแปลง `.lib` → `.kicad_sym` ผ่าน kicad-cli
- Footprint (`.kicad_mod`) — พร้อม upgrade ผ่าน kicad-cli
- 3D model (`.step`, `.stp`, `.wrl`) — รองรับ gzip compress (`step.gz`)
- DCM (คำอธิบาย component)

## กระแสการทำงาน (Data Flow)

### 1. Auto Import (Monitor Folder)
```
User วาง ZIP ใน source folder
    → FileHandler.get_new_files() ตรวจจับไฟล์ใหม่
    → LibImporter.import_all() เรียกทีละไฟล์
        → identify_remote_type() ตรวจสอบชนิด
        → load_symbol_lib() → extract → แปลง .lib → .kicad_sym (optional)
        → extract_footprint_to_file() → extract → upgrade → วางใน .pretty
        → load_model() → extract 3D model
        → update_symbol_properties() → ใส่ footprint reference
        → save_to_library() → backup → atomic write → cleanup
    → check_library_import() → ตรวจสอบ sym-lib-table/fp-lib-table → เตือน
```

### 2. Manual EasyEDA Import
```
User ป้อน LCSC Part# (เช่น C2040)
    → EasyEDAImporter.import_component()
        → EasyedaApi.get_cad_data_of_component()
        → import_symbol() → ExporterSymbolKicad
        → import_footprint() → ExporterFootprintKicad
        → import_3d_model() → Exporter3dModelKicad (optionally gzip)
    → KiCad_Settings.check_symbollib/check_footprintlib → ตรวจสอบ/เพิ่มใน table
```

### 3. Drag & Drop
```
User ลาก ZIP → วางบน text control
    → FileDropTarget.OnDropFiles()
    → _import_dropped_files()
        → _update_backend_settings()
        → _import_single_file() (เหมือน auto import)
        → _check_and_show_library_warnings()
```

### 4. Component Search (JLCPCB)
```
User ค้นหาชื่อชิ้นส่วน
    → EasyedaApi.search_jlcpcb_components() (API)
    → แสดงผลใน ListCtrl (auto-resize columns ตามสัดส่วน)
    → เลือกรายการ → show_component() → สร้าง cards:
        Basic Info → Stock & Pricing → Actions → Technical Specs → Previews
    → fetch product image (async) → set_image() → _rewrap_all_texts()
    → กด Import → _on_import_clicked() → disable btn → "Importing..."
        → _wrap_import() → set_status → _on_import_cb()
        → _perform_easyeda_import() → return bool
        → MessageBox Success/Error → restore btn
    → กด Open Datasheet/Product Page → _open_url() → browser
```

## โครงสร้างคลาสสำคัญ

### impart_action.py
- **`ImpartFrontend(impartGUI)`** — Main dialog:
  - `fallback_mode`: True เมื่อเรียกจาก pcbnew, False เมื่อ standalone
  - `on_close()`: จัดการปิด 3 แบบ (ไม่มี auto import / มี → hide / มี → stop)
  - `BottonClick()`: เริ่ม/หยุด auto import
  - `ButtomManualImport()`: EasyEDA import
  - `DirChange()`: เปลี่ยน source/destination path
  - `_safe_cleanup()`: cleanup ที่ปลอดภัย (save → stop thread → close IPC)

- **`ImpartBackend`** — Business logic:
  - สร้าง `KiCadApp`, `ConfigHandler`, `KiCad_Settings`, `FileHandler`, `LibImporter`
  - `find_and_import_new_files()`: วน loop ตรวจจับไฟล์ใหม่
  - `print_to_buffer()`: สะสมข้อความให้ PluginThread อ่าน

- **`PluginThread(Thread)`** — Daemon thread สำหรับ monitor status:
  - ตรวจสอบ `print_buffer` ทุก 0.5 วินาที
  - ส่ง `ResultEvent` ผ่าน `wx.PostEvent`

### component_search.py
- **`DetailPanel(wx.ScrolledWindow)`** — Card-based detail view (ฝั่งขวาของ splitter):
  - Cards (เรียงจากบนลงล่าง): Basic Info → Stock & Pricing → Actions → Technical Specs → Previews
  - `show_component(row)`: สร้าง cards ใหม่ทั้งหมด, ตั้งค่า `_current_lcsc`, wrap text ครั้งแรก
  - `set_image(data)`: ตั้งรูปสินค้า (async) → `_rewrap_all_texts()` re-wrap ข้อความ
  - `_on_import_clicked(event)`: disable btn → "Importing..." → `Update()` → callback → restore
  - `_rewrap_all_texts()`: traverse children StaticText → `Wrap(current_width)` → Layout (loop สูงสุด 3 รอบจน stable)
  - `_walk_and_wrap(parent)`: static method recursive walk children
  - `clear()`: ทำลาย cards ทั้งหมด → แสดง placeholder
  - `_open_url(url)`: เปิด URL ใน external browser

- **`SearchPanel(wx.Panel)`** — หน้าค้นหาหลัก:
  - Search bar + Filter button + ListCtrl (auto-resize columns) + DetailPanel (splitter)
  - `_build_ui()`: สร้าง UI + wx.CallAfter(`_auto_resize_columns`)
  - `_on_search()`: ส่ง API request แบบ async thread → `_search_done()` → `_apply_filters()`
  - `_on_item_selected()`: แสดง detail + fetch image + callback `on_select(lcsc)`
  - `_wrap_import(lcsc)`: set_status("Importing...") → `_on_import_cb()` → set_status("")
  - `_auto_resize_columns()`: กระจาย extra space ตามสัดส่วน min_width
  - `_populate_list()`: เติม ListCtrl จาก `self._results`
  - `_apply_filters()`: กรองตาม FilterState (brand, package, type, stock, price)
  - FilterState: excluded_brands/packages/types, min_stock, min_price, max_price
  - COLUMNS: 7 คอลัมน์ (LCSC#, Name, Brand, Package, Stock, Type, Price) พร้อม min_width

- **`SearchDialog(wx.Dialog)`** — Dialog wrapper:
  - เปิด 85% × 80% ของหน้าจอ
  - `on_select`: callback เมื่อคลิกแถว (เติม LCSC# ใน main GUI)
  - `on_import`: callback เมื่อกด Import (เรียก `_quick_import` ซึ่ง sync settings → `_perform_easyeda_import`)
  - `get_lcsc()`: คืนค่า LCSC# ของแถวที่เลือก

- **`FilterDialog(wx.Dialog)`** — Dialog กรองผลลัพธ์:
  - Brand/Package/Type: CheckListBox (exclude mode)
  - Numeric: Min Stock, Min Price, Max Price
  - Reset button + OK/Cancel

### single_instance_manager.py
- **`SingleInstanceManager`**:
  - `is_already_running()`: bind TCP port → ถ้าล้มเหลวส่ง focus command
  - `start_server()`: เริ่ม thread สำหรับรับ TCP connection
  - `_bring_to_foreground()`: Iconize → Restore → Raise → SetFocus
  - `stop_server()`: shutdown socket + join thread

### KiCadSettingsPaths (KiCadSettingsPaths/__init__.py)
- **`KiCadSettingsPaths`** — static methods สำหรับหา KiCad settings path
- **`KiCadVersionInfo`** — container สำหรับ version
- **`KiCadProjectInfo`** — container สำหรับ project info
- **`KiCadApp`** — Unified interface สำหรับ KiCad interaction:
  - `connection_type`: "IPC", "SWIG", "FALLBACK"
  - `_try_init_ipc()`: ลอง `kipy.KiCad()` ก่อน
  - `_try_init_swig()`: fallback เป็น `pcbnew`
  - `_find_project_via_process_args()`: ใช้ psutil → proc scan เป็นทางเลือกสุดท้าย

### KiCad_Settings (KiCad_Settings/__init__.py)
- **`KiCad_Settings`** — จัดการไฟล์:
  - `sym-lib-table` / `fp-lib-table` (ผ่าน kiutils.LibTable)
  - `kicad_common.json` (environment variables)
  - `kicad.json`
  - `check_symbollib()` / `check_footprintlib()`: ตรวจสอบ + เพิ่มอัตโนมัติ
  - `check_GlobalVar()`: ตรวจสอบ KICAD_3RD_PARTY environment variable

### KiCadImport (KiCadImport/__init__.py)
- **`LibImporter`** — กลไกหลัก:
  - `identify_remote_type()`: วิเคราะห์ ZIP → ระบุ source + หา path ไฟล์
  - `load_symbol_lib()`: แยก symbol → แปลง .lib → .kicad_sym ผ่าน kicad-cli
  - `extract_footprint_to_file()`: แยก footprint → upgrade ผ่าน kicad-cli
  - `save_to_library()`: บันทึกแบบ atomic + backup/rollback
  - `import_all()`: จุดรวมทุกอย่าง

### kicad_cli (kicad_cli/__init__.py)
- **`KicadCli`** — Wrapper รอบ `kicad-cli`:
  - ค้นหา CLI path (macOS absolute + PATH)
  - `exists()`: ตรวจสอบ version ≥ 8.0.4
  - `upgrade_sym_lib()`: `kicad-cli sym upgrade`
  - `upgrade_footprint_lib()`: `kicad-cli fp upgrade`
  - `upgrade_sym_lib_from_string()`: upgrade จาก string (ใช้ temp file)
  - รองรับ `CREATE_NO_WINDOW` บน Windows, force locale `en_US.UTF-8`
  - มี backup/rollback ถ้า in-place upgrade

## การจัดการ Path

### KiCad Settings Path (OS-specific)
| OS | Default Path |
|----|-------------|
| Windows | `%APPDATA%/kicad` หรือ `%APPDATA%/kicad/{version}` |
| macOS | `~/Library/Preferences/kicad` |
| Linux | `~/.config/kicad` หรือ `$XDG_CONFIG_HOME/kicad` |

### Path Variable
- `KICAD_3RD_PARTY` — สำหรับ global library (ค่าเริ่มต้น)
- `KIPRJMOD` — สำหรับ project-specific library (เมื่อเลือก local lib)

## การใช้ Git Submodules
Repo มี 2 submodules:
- `plugins/kiutils` → `github.com/Steffen-W/kiutils.git` (branch: master) — fork จาก KiCad
- `plugins/easyeda2kicad` → `github.com/Steffen-W/easyeda2kicad.py.git` (branch: master) — fork จาก uPesy

หลัง clone ต้องรัน: `git submodule update --init --recursive`

Submodules ถูก import ผ่าน `sys.path.insert(0, ...)` ไม่ได้ผ่าน pip

## Library Scanner (library_scanner.py)
เพิ่มใหม่สำหรับ Library Browser — scan destination path เพื่อหารายการ library ที่ import แล้ว:

- `LibraryScanner(dest_path)` — constructor
- `scan_symbols()` → `list[SymbolEntry]` — scan `.kicad_sym` files
- `scan_footprints()` → `list[FootprintEntry]` — scan `.pretty/` directories
- `scan_models()` → `list[ModelEntry]` — scan `.3dshapes/` directories
- `scan_all()` → `dict` รวมทั้งสามประเภท
- `get_summary()` → นับจำนวน

กรณี `kiutils` ไม่พร้อมใช้งาน จะ fallback เป็น regex อ่านชื่อ symbol จาก content ไฟล์

### Encoding fallback (สำคัญสำหรับ EXE)
`_read_symbol_names()` ลองอ่าน `.kicad_sym` หลาย encoding เรียงลำดับ:
1. `utf-8` — ลองก่อน เพราะ KiCad sym-lib-table ใช้ UTF-8
2. `None` — platform default (ต่างกันระหว่าง Python ปกติ vs PyInstaller EXE)
3. `cp1252` — Windows Western European ถ้า encoding ก่อนหน้า failed

ถ้าทั้งหมด failed → fallback เป็น regex (`r'\(symbol\s+"([^"]*)"'`)
⚠️ regex fallback จะนับรวม `_0_1` suffix entries (KiCad duplicate name resolution) ทำให้จำนวน symbol สูงกว่าความเป็นจริง

## Library Browser Dialog (library_browser.py)
`LibraryBrowserDialog(wx.Dialog)` — มี `wx.Notebook` 3 tabs:
1. **Symbols** — ชื่อ lib, จำนวน symbol, ขนาด KB, source
2. **Footprints** — ชื่อ lib, จำนวน footprint, source
3. **3D Models** — ชื่อ lib, จำนวนไฟล์, format (step/wrl/step.gz)

คลิก "Show Details" → `DetailDialog` แสดงรายชื่อย่อยทั้งหมด (symbol names, footprint names, model filenames)

### Relative import fallback
ต้องมี try/except สำหรับ relative import เพราะ `run_standalone.bat` เรียก script โดยตรง:
```python
try:
    from .library_scanner import LibraryScanner
except ImportError:
    from library_scanner import LibraryScanner
```

## การจัดการ config
ใช้ `ConfigHandler` (ตั้งชื่อเป็น "config handler" ไม่ใช่ "config handler" ตาม PEP8 เพื่อคงความเข้ากันได้):
```
[config]
src_path = {HOME}/Downloads
dest_path = {HOME}/KiCad
```
Settings เพิ่มเติม (auto_import, overwrite_import, auto_lib, local_lib, single_lib, lib_name, compress_models) ถูก save ที่ section เดียวกัน

### Config persistence ใน EXE mode
เมื่อรันเป็น EXE (`sys.frozen = True`):
- Config path = `{exe_dir}/config.ini` (ข้าง `impartGUI.exe` ใน `dist/`)
- รอบแรก: copy config จาก `_MEIPASS/plugins/config.ini` (PyInstaller temp) → `dist/config.ini`
- รอบถัดไป: อ่านจาก `dist/config.ini` โดยตรง
- ตอน save: เขียนกลับที่ `dist/config.ini` เดิม → ค่าคงอยู่ถาวร

⚠️ ถ้า config.ini ไม่ถูก include ใน EXE (`--add-data`) โปรแกรมจะใช้ default path เสมอ (`~/KiCad`)
ซึ่งอาจต่างจาก path ที่ผู้ใช้ตั้งไว้ใน `run_standalone.bat`

### Debug log toggle
มี config `debug_log` (True/False) สำหรับเปิด/ปิด DEBUG logging:
- ค่าเริ่มต้น: `False` (แสดงเฉพาะ INFO ขึ้นไป)
- เปลี่ยนเป็น `True` ใน `config.ini` เพื่อดู debug messages ทั้งหมด
- มีผลหลังจากรีสตาร์ทโปรแกรมเท่านั้น (อ่านค่าเฉพาะตอน startup)

## เคล็ดลับการ debug
1. log file หลัก (standalone): `plugins/plugin.log`
2. log file หลัก (EXE): `dist/plugin.log` (ข้าง executable)
3. fallback log: `plugins/plugin_fallback.log`
4. เปิด debug mode: ตั้ง logger level DEBUG
5. ทดสอบแบบ standalone: `python -c "from plugins.impart_action import ImpartFrontend; import wx; app=wx.App(); f=ImpartFrontend(); f.ShowModal()"`
6. ทดสอบ CLI import: `python -m plugins.KiCadImport --download-file test.zip --lib-folder output/`
7. EXE: log ทุกอย่างถูก force flush ทันที (ไม่ต้องปิดโปรแกรมถึงจะเห็น log)

## วิธีรัน standalone
ใช้ `run_standalone.bat` (Windows) — หา Python จาก:
1. `C:\Program Files\KiCad\10.0\bin\python.exe`
2. `C:\Program Files\KiCad\9.0` / `8.0` / `nightly`
3. `%KICAD_PYTHON_PATH%` environment variable
4. `python` ใน PATH

จากนั้น auto-install: `kiutils` + `easyeda2kicad` ถ้ายังไม่มี

## ข้อควรระวัง
- `impart_gui.py` ถูก generate โดย wxFormBuilder — ห้ามแก้ไขตรง ต้องแก้ .fbp แล้ว gen ใหม่
- การ import แบบ `.lib` (legacy) ต้องมี kicad-cli installed
- footrint upgrade ผ่าน kicad-cli ต้องใช้ `.pretty` folder structure
- ถ้า psutil ไม่ได้ install บน Windows จะไม่สามารถ detect project path ได้
- Windows path อาจมี spaces → ใช้ Path object เสมอ
- submodule update อาจ broken ถ้ามี local changes

## ตัวแปร environment ที่สำคัญ
- `VIRTUAL_ENV` — ใช้ใน `_setup_venv_path()` สำหรับ IPC API
- `LANG`, `LC_ALL` — ถูก force เป็น `en_US.UTF-8` สำหรับ kicad-cli
- `KICAD_3RD_PARTY` — path variable สำหรับ 3rd party libraries
