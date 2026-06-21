# AGENT.MD — แนวทางการพัฒนา Import-LIB-KiCad-Plugin

## ภาพรวมโปรเจกต์
KiCad Plugin สำหรับนำเข้าห้องสมุดชิ้นส่วน (library) จาก Octopart, Samacsys, UltraLibrarian, SnapEDA และ EasyEDA/LCSC
รองรับสัญลักษณ์ (symbol), ฟุตพริ้นท์ (footprint), โมเดล 3 มิติ และคำอธิบาย (DCM)

## สถาปัตยกรรม

```
plugins/
├── impart_action.py          # Frontend + Backend + Event/Close logic
├── impart_gui.py             # GUI ที่เกิดจาก wxFormBuilder (ห้ามแก้ไขตรง ๆ)
├── impart_easyeda.py         # EasyEDA/LCSC import (ผ่าน easyeda2kicad submodule)
├── component_search.py       # ค้นหาชิ้นส่วน JLCPCB แบบ GUI + API
├── single_instance_manager.py# จัดการ single instance ด้วย TCP socket
├── __init__.py               # pcbnew.ActionPlugin fallback entry
├── __main__.py               # รันแบบ standalone (wx.App)
├── ConfigHandler/            # อ่าน/เขียน config.ini
├── FileHandler/              # ตรวจจับไฟล์ ZIP ใหม่ในโฟลเดอร์
├── KiCad_Settings/           # จัดการ sym-lib-table / fp-lib-table / kicad_common.json
├── KiCadSettingsPaths/       # ตรวจหา KiCad settings path + KiCadApp (IPC/SWIG)
├── KiCadImport/              # กลไกหลักในการ import ZIP → KiCad library
├── kicad_cli/                # Wrapper รอบ `kicad-cli` (subprocess)
├── kiutils/                  # Git submodule (fork)
└── easyeda2kicad/            # Git submodule (fork)
```

## กฎเหล็กในการเขียน code

### 1. การ import
- ใช้ `from __future__ import annotations` เสมอ
- ลอง relative import ก่อน (`from .Foo import Bar`) ถ้าไม่ได้ค่อย fallback เป็น absolute
- จัดการ `sys.path` สำหรับ submodule ด้วยตัวเอง (ไม่ใช้ venv)

### 2. รูปแบบการเชื่อมต่อ KiCad
มี 2 แบบ ทำงานคู่กัน:

| โหมด | คลาส | วิธี |
|------|-------|------|
| IPC (kipy) | `KiCadApp` → `kicad_ipc` | ผ่าน `kipy.KiCad()` — ได้ project info, version |
| SWIG (pcbnew) | `KiCadApp` → `pcbnew` | ผ่าน `pcbnew.GetBoard()` — fallback ถ้า IPC ไม่ได้ |
| Fallback | `ActionImpartPlugin` | `pcbnew.ActionPlugin` — ใช้ใน `__init__.py` |

### 3. รูปแบบการรัน
- **IPC mode**: `python plugins\__main__.py` — มี singleton, TCP window focus
- **Fallback mode**: เรียกจาก `pcbnew.ActionPlugin` — สร้าง instance ใหม่เสมอ
- ทั้งสองแบบใช้ `ImpartFrontend` เหมือนกัน ต่างกันที่ `fallback_mode` flag

### 4. การจัดการ single instance
ใช้ TCP socket (`single_instance_manager.py`):
- ผูก port ที่คำนวณจาก hash ของ path plugin
- instance แรก bind socket, instance หลังส่ง `"focus\n"` แล้ว exit
- port range: 49152–65534

### 5. Thread safety
- ห้ามแตะ wx objects นอก main thread
- ใช้ `wx.PostEvent()` + `ResultEvent` สำหรับส่งข้อมูลจาก thread ไป GUI
- ใช้ `wx.CallAfter()` สำหรับเรียกฟังก์ชันใน main thread

### 6. Error handling
- ทุก exception ต้อง log ด้วย `logger.exception()`
- ฟังก์ชันอาจมี 2 return path สำเร็จ/ล้มเหลว — ต้องจัดการทั้งคู่
- show_error_dialog() สำหรับ user-facing error, มี fallback เป็น print

### 7. File I/O
- ใช้ `pathlib.Path` เสมอ ไม่ใช้ `os.path` ยกเว้นจำเป็น
- atomic write: เข้า temp file → verify → rename
- backup/rollback สำหรับ critical operations
- cleanup temp dirs ใน `finally` block

### 8. Config
- `config.ini` ใช้ `configparser` (ไม่ใช่ JSON)
- ค่าเริ่มต้นผ่าน `ConfigHandler.defaults`
- plugin.json สำหรับ KiCad PCM manifest
- metadata.json สำหรับ PCM version info

### 9. GUI conventions
- `impart_gui.py` ห้ามแก้ไขตรง (wxFormBuilder gen)
- event handler methods ใช้ชื่อตาม wxFormBuilder convention เช่น `BottonClick`, `DirChange`
- ทุก handler ต้องเรียก `event.Skip()` ยกเว้น veto จริง ๆ

## CI / Lint / Type Check
```bash
ruff check plugins                    # lint (target py39, line-length 100)
ruff format --check plugins           # format check
mypy plugins                          # type check
pyright                               # type check (config ใน pyrightconfig.json)
```

### ประเภทของ library source
```
REMOTE_TYPES:
  Octopart       → device.lib + device.dcm + .pretty โฟลเดอร์
  Samacsys       → KiCad/ โฟลเดอร์ + .kicad_sym
  UltraLibrarian → KiCAD/ โฟลเดอร์ + .kicad_sym
  Snapeda        → .kicad_sym + .kicad_mod (flat structure)
  Partial        → มีแค่ 3D model ไม่มี symbol/footprint
```

## การเพิ่มฟีเจอร์ใหม่
1. ตรวจสอบ `KiCadApp` ว่าต้องเพิ่ม connection type หรือไม่
2. ถ้าเพิ่ม source library → เพิ่มใน `REMOTE_TYPES`, `identify_remote_type()`, `SUPPORTED_LIBRARIES`
3. ถ้าเพิ่ม GUI element → แก้ wxFormBuilder .fbp แล้ว re-generate `impart_gui.py`
4. ถ้าเพิ่ม setting → เพิ่มใน `config.ini`, `_setup_gui()`, `_save_settings()`, `_update_backend_settings()`
5. ทดสอบทั้ง IPC mode และ fallback mode

## Patterns ที่ใช้ใน component_search.py

### Callback chain (on_select / on_import)
```
SearchDialog(on_select=..., on_import=...)
  → SearchPanel(on_select=cb, on_import=cb)
    → DetailPanel(on_import=wrapped_cb)
```
- `on_select`: เรียกเมื่อคลิกแถว ListCtrl — ส่ง LCSC# ไป fill field หน้าหลัก
- `on_import`: เรียกเมื่อกด Import ใน Actions card — ควร wrap ด้วย `_wrap_import()` เพื่อ update status
- `_wrap_import()`: set_status → Update() → real callback → set_status("")

### Button visual feedback (synchronous import)
```python
btn.Disable()
btn.SetLabel("Importing...")
btn.Update()       # force immediate repaint
try:
    callback()     # blocking import (main thread)
finally:
    btn.Enable()
    btn.SetLabel("Import to KiCad")
```

### Variable naming: ระวัง shadowing
ใน `show_component(self, row)` ห้ามใช้ `row` เป็นชื่อ sizer/ตัวแปรอื่น — `row` คือ parameter ที่เป็น dict ของ component data
```python
# ❌ row = wx.BoxSizer(wx.HORIZONTAL)   → shadow! cascade fail
# ✅ btn_row = wx.BoxSizer(wx.HORIZONTAL)
```

### ListCtrl auto-resize columns
```python
def _auto_resize_columns(self):
    base = [COLUMNS[i][2] for i in range(col_count)]
    extra = total - sum(base)
    # กระจาย extra ตามสัดส่วน min_width
    for i in range(col_count - 1):
        w = base[i] + int(extra * base[i] / total_base)
    # คอลัมน์สุดท้ายรับเศษ rounding
```
เรียกที่ `wx.CallAfter(self._auto_resize_columns)` หลัง build UI + `EVT_SIZE`

### Text re-wrap (เมื่อ layout เปลี่ยนจาก image)
```python
DetailPanel._rewrap_all_texts():
    for _ in range(3):  # loop จน stable
        _walk_and_wrap(self)  # recursive → Wrap(child.GetSize().width)
        Layout() + FitInside()
```
เรียกตอนท้าย `show_component()` และใน `set_image()` หลัง image show/hide

### `_perform_easyeda_import()` return bool
คืน `True` เมื่อ import สำเร็จ, `False` เมื่อ error — caller ใช้ตรวจสอบ success เพื่อแสดง MessageBox

## ไฟล์ใหม่ที่เพิ่ม: Library Browser

## ไฟล์ใหม่ที่เพิ่ม: Library Browser

| ไฟล์ | บทบาท |
|------|--------|
| `plugins/library_scanner.py` | Scanner backend — scan `.kicad_sym`, `.pretty/`, `.3dshapes/` จาก destination path มี fallback regex ถ้า `kiutils` ไม่มี |
| `plugins/library_browser.py` | `LibraryBrowserDialog(wx.Dialog)` — 3-tab notebook แสดงรายการ พร้อม `DetailDialog` แสดงชื่อ symbol/footprint/model |

### Relative import fallback
ไฟล์ที่ import module ใน package เดียวกันต้องมี try/except fallback:
```python
try:
    from .library_scanner import LibraryScanner
except ImportError:
    from library_scanner import LibraryScanner
```
ทั้งนี้เพราะ `run_standalone.bat` เรียก script โดยตรง (ไม่ใช่ `-m`)

## การ run standalone
ใช้ `run_standalone.bat` — หา KiCad Python อัตโนมัติ + ลง dependencies:
- `kiutils` — จำเป็น (fallback regex มี แต่ kiutils ให้ข้อมูลครบ)
- `easyeda2kicad` — สำหรับ EasyEDA import

## การ build EXE (Windows)
ใช้ `build_exe.bat` — สร้าง `dist/impartGUI.exe` ด้วย PyInstaller:

### Hidden imports ที่ต้องระบุ
- `ConfigHandler`, `FileHandler`, `impart_gui`, `KiCad_Settings`, `KiCadImport`
- `KiCadSettingsPaths`, `kicad_cli`, `component_search`
- `easyeda2kicad.easyeda.easyeda_api`, `kiutils`

### Data files ที่ต้อง include
- `icon.png` — ใช้เป็น icon ในหน้าต่าง
- `config.ini` — include เพื่อให้ EXE มีค่า default ตอนแรก

### Config persistence (frozen mode)
เมื่อรันเป็น EXE (`sys.frozen=True`):
- Config path = `{exe_dir}/config.ini` (ข้าง executable, ไม่ใช่ temp dir)
- รอบแรก: copy config จาก temp dir (`_MEIPASS/plugins/config.ini`) ไปที่ exe_dir
- หลังจากนั้น: อ่าน/เขียนจาก exe_dir โดยตรง — config อยู่ถาวร

### Encoding issue: kiutils + regex fallback
เมื่อ kiutils อ่าน `.kicad_sym` ไม่ผ่าน (encoding error ใน EXE):
- `_read_symbol_names()` จะลองหลาย encoding: `utf-8` → `None` → `cp1252`
- ถ้าทั้งหมด failed → fallback เป็น regex
- regex นับ `(symbol "NAME")` ทุกอันรวมถึง `_0_1` (KiCad duplicate) → ตัวเลขสูงกว่าความเป็นจริง

## การ build/distribute (ZIP)
ใช้ `generate_zip.sh` (ต้องการ bash, jq, zip):
- จัดการ submodule auto-init/update
- แกะเฉพาะส่วนที่จำเป็นของ submodule
- สร้าง ZIP สำหรับ PCM
