<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://github.com/user-attachments/assets/b5c65f6f-7612-4883-9032-aaf6e16cc782">
  <img alt="impart GUI for KiCad" src="https://github.com/user-attachments/assets/b5c65f6f-7612-4883-9032-aaf6e16cc782" width="648">
</picture>

![Static Badge](https://img.shields.io/badge/KiCad-8.0_|_9.0_|_10.0-blue?logo=kicad&logoColor=white)
![Static Badge](https://img.shields.io/badge/Platform-Windows_|_macOS_|_Linux-green)
![Static Badge](https://img.shields.io/badge/Python-3.9_|_3.10_|_3.11_|_3.12-blue?logo=python&logoColor=white)
![GitHub Release](https://img.shields.io/github/v/release/Steffen-W/Import-LIB-KiCad-Plugin?logo=github)
![GitHub Downloads](https://img.shields.io/github/downloads/Steffen-W/Import-LIB-KiCad-Plugin/total)
![License](https://img.shields.io/github/license/Steffen-W/Import-LIB-KiCad-Plugin)

[![Samacsys](https://img.shields.io/badge/Samacsys-Compatible-1e8449)](https://componentsearchengine.com)
[![SnapEDA](https://img.shields.io/badge/SnapEDA-Compatible-27ae60)](https://www.snapeda.com)
[![UltraLibrarian](https://img.shields.io/badge/UltraLibrarian-Compatible-229954)](https://app.ultralibrarian.com)
[![Octopart](https://img.shields.io/badge/Octopart-Compatible-52be80)](https://octopart.com)
[![LCSC/EasyEDA](https://img.shields.io/badge/LCSC_EasyEDA-Compatible-008000)](https://www.lcsc.com)

---

Plugin สำหรับนำเข้า library ชิ้นส่วนอิเล็กทรอนิกส์จาก Octopart, Samacsys, UltraLibrarian, SnapEDA และ EasyEDA/LCSC เข้าสู่ KiCad โดยตรง รองรับการนำเข้าสัญลักษณ์ (symbols), ฟุตพริ้นท์ (footprints), คำอธิบาย (descriptions) และโมเดล 3 มิติ (3D files) พร้อมลิงก์ทุกอย่างให้พร้อมใช้งานทันที

---

## สารบัญ

- [คุณสมบัติ](#คุณสมบัติ)
- [ความต้องการของระบบ](#ความต้องการของระบบ)
- [การติดตั้ง](#การติดตั้ง)
  - [ติดตั้งผ่าน PCM (แนะนำ)](#ติดตั้งผ่าน-pcm-แนะนำ)
  - [ติดตั้งด้วย ZIP](#ติดตั้งด้วย-zip)
  - [ติดตั้งจาก source](#ติดตั้งจาก-source)
- [การตั้งค่า KiCad](#การตั้งค่า-kicad)
  - [ตั้งค่า Environment Variable](#ตั้งค่า-environment-variable)
  - [เพิ่ม Symbol Libraries](#เพิ่ม-symbol-libraries)
  - [เพิ่ม Footprint Libraries](#เพิ่ม-footprint-libraries)
- [การใช้งาน](#การใช้งาน)
  - [ใช้งานภายใน KiCad](#ใช้งานภายใน-kicad)
  - [ใช้งานแบบ Standalone (ไม่ต้องเปิด KiCad)](#ใช้งานแบบ-standalone-ไม่ต้องเปิด-kicad)
  - [Drag & Drop](#drag--drop)
  - [Library Browser](#library-browser)
  - [Component Search (JLCPCB/EasyEDA)](#component-search-jlcpcbeasyeda)
- [CLI Mode](#cli-mode)
- [การตั้งค่า](#การตั้งค่า)
- [การแก้ไขปัญหา](#การแก้ไขปัญหา)
- [การพัฒนา](#การพัฒนา)
- [เครดิต](#เครดิต)

---

## คุณสมบัติ

- **นำเข้า Library จาก 5 แหล่ง:** Octopart, Samacsys, UltraLibrarian, SnapEDA, EasyEDA/LCSC
- **Auto Import:** ตรวจสอบโฟลเดอร์ที่กำหนดโดยอัตโนมัติและนำเข้าไฟล์ ZIP ใหม่ทันที
- **Library Browser:** ดูรายการ Symbols, Footprints และ 3D Models ที่นำเข้าแล้ว
- **Component Search:** ค้นหาชิ้นส่วน JLCPCB/EasyEDA และนำเข้าได้ทันที
- **Drag & Drop:** ลากไฟล์ ZIP วางลงบนหน้าต่างเพื่อนำเข้าทันที
- **KiCad CLI Integration:** ใช้ kicad-cli อัปเกรด library เป็นรูปแบบล่าสุด
- **IPC API (แนะนำ):** เชื่อมต่อกับ KiCad ผ่าน IPC API ที่ทันสมัย
- **Fallback Mode:** ทำงานผ่าน pcbnew ได้หากไม่มี IPC API
- **Single Instance:** ป้องกันการเปิดหน้าต่างซ้ำซ้อน
- **ข้ามแพลตฟอร์ม:** ทำงานบน Windows, macOS และ Linux
- **Standalone Launcher:** เรียกใช้โดยไม่ต้องเปิด KiCad (Windows)

---

## ความต้องการของระบบ

| ข้อกำหนด | รายละเอียด |
|-----------|-----------|
| KiCad | 8.0, 9.0 หรือ 10.0 |
| Python | 3.9, 3.10, 3.11 หรือ 3.12 |
| ระบบปฏิบัติการ | Windows 10+, macOS, Linux |
| wxPython | ต้องมี (มาพร้อม KiCad) |
| kicad-cli | แนะนำสำหรับอัปเกรด library |

---

## การติดตั้ง

### ติดตั้งผ่าน PCM (แนะนำ)

1. เปิด KiCad → **Tools** → **Plugin and Content Manager**
2. เลือกแท็บ **Plugins** → ค้นหา **impart GUI for KiCad**
3. กด **Install** → **Apply Pending Changes**

### ติดตั้งด้วย ZIP

1. ดาวน์โหลดไฟล์ `Import-LIB-KiCad-Plugin.zip` ล่าสุดจาก [GitHub Releases](https://github.com/Steffen-W/Import-LIB-KiCad-Plugin/releases/latest)
2. เปิด KiCad → **Tools** → **Plugin and Content Manager**
3. กด **Install from File...** → เลือกไฟล์ ZIP ที่ดาวน์โหลดมา
4. กด **Apply Pending Changes**

### ติดตั้งจาก source

```bash
# Clone พร้อม submodules
git clone --recurse-submodules https://github.com/Steffen-W/Import-LIB-KiCad-Plugin.git
cd Import-LIB-KiCad-Plugin

# หรือถ้า clone แล้วลืม --recurse-submodules
git submodule update --init

# ติดตั้ง dependencies ที่จำเป็น
pip install kiutils easyeda2kicad

# สร้าง ZIP package
# Windows:
generate_zip.bat
# Linux/macOS:
./generate_zip.sh
```

---

## การตั้งค่า KiCad

### ตั้งค่า Environment Variable

**Preferences** → **Configure Paths** → **Environment Variables** → Add new entry:

| Name | Path |
|------|------|
| `KICAD_3RD_PARTY` | `โฟลเดอร์ที่คุณใช้เก็บ library`/KiCad |

> ตัวอย่าง: `C:\Users\คุณ\KiCad`

### เพิ่ม Symbol Libraries

**Preferences** → **Manage Symbol Libraries** → **Global Libraries** → Add entries:

| Nickname | Library Path | Format |
|----------|-------------|--------|
| Samacsys | `${KICAD_3RD_PARTY}/Samacsys.kicad_sym` | KiCad |
| Snapeda | `${KICAD_3RD_PARTY}/Snapeda.kicad_sym` | KiCad |
| UltraLibrarian | `${KICAD_3RD_PARTY}/UltraLibrarian.kicad_sym` | KiCad |
| Octopart | `${KICAD_3RD_PARTY}/Octopart.kicad_sym` | KiCad |
| EasyEDA | `${KICAD_3RD_PARTY}/EasyEDA.kicad_sym` | KiCad |

### เพิ่ม Footprint Libraries

**Preferences** → **Manage Footprint Libraries** → **Global Libraries** → Add entries:

| Nickname | Library Path | Format |
|----------|-------------|--------|
| Samacsys | `${KICAD_3RD_PARTY}/Samacsys.pretty` | KiCad |
| Snapeda | `${KICAD_3RD_PARTY}/Snapeda.pretty` | KiCad |
| UltraLibrarian | `${KICAD_3RD_PARTY}/UltraLibrarian.pretty` | KiCad |
| Octopart | `${KICAD_3RD_PARTY}/Octopart.pretty` | KiCad |
| EasyEDA | `${KICAD_3RD_PARTY}/EasyEDA.pretty` | KiCad |

> **หมายเหตุ:** Add เฉพาะ library ที่คุณจะใช้เท่านั้น library ที่ยังไม่มีไฟล์จะแสดง error แต่จะหายไปเมื่อ import ครั้งแรก

### ตั้งค่า Plugin System (IPC API)

1. **KiCad** → **Settings** → **Plugins** → **Enable Plugin System**
2. เปิด **Enable KiCad API**
3. Restart KiCad

เมื่อเปิด IPC API แล้ว plugin จะมี 2 โหมดในเมนู:
- **impartGUI (IPC API)** — โหมดแนะนำ ใช้ IPC API
- **impartGUI** — Fallback mode ใช้ pcbnew

---

## การใช้งาน

### ใช้งานภายใน KiCad

1. เปิด **PCB Editor** หรือ **Schematic Editor**
2. **Tools** → **External Plugins** → **impartGUI (IPC API)**
3. ตั้งค่า:
   - **Folder of the library to import:** โฟลเดอร์ที่เก็บไฟล์ ZIP ที่ดาวน์โหลดมา
   - **Library save location:** โฟลเดอร์ปลายทางสำหรับ library ที่ import (ควรเป็นที่เดียวกับ `KICAD_3RD_PARTY`)
   - กด **Start** เพื่อเริ่ม Auto Import

### ใช้งานแบบ Standalone (ไม่ต้องเปิด KiCad)

มีประโยชน์เมื่อคุณต้องการ import library โดยไม่ต้องรัน KiCad หรือเมื่อ KiCad API ไม่พร้อมใช้งาน

#### Windows

ใช้ `run_standalone.bat` ที่มาพร้อมกับ plugin:

```batch
run_standalone.bat
```

สคริปต์จะ:
1. ค้นหา KiCad Python (10.0 → 9.0 → 8.0 → nightly → PATH)
2. ตรวจสอบ wxPython (ถ้าไม่มีจะแจ้ง error)
3. ติดตั้ง `kiutils` และ `easyeda2kicad` อัตโนมัติ (ถ้ายังไม่มี)
4. เปิดหน้าต่าง impartGUI

#### macOS / Linux

```bash
# หา Python ที่มากับ KiCad
python3 plugins/impart_action.py

# หรือใช้ virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install kiutils easyeda2kicad wxPython
python3 plugins/impart_action.py
```

### Drag & Drop

ลากไฟล์ ZIP จาก File Explorer หรือ Finder แล้ววางลงในพื้นที่ข้อความของหน้าต่าง impartGUI เพื่อนำเข้าทันทีโดยไม่ต้องตั้งค่าโฟลเดอร์ monitoring

### Library Browser

กดปุ่ม **Library Browser** เพื่อเปิดหน้าต่างเรียกดู library ที่นำเข้าแล้วทั้งหมด:
- **แท็บ Symbols:** แสดง .kicad_sym พร้อมรายชื่อสัญลักษณ์
- **แท็บ Footprints:** แสดง .pretty พร้อมรายชื่อฟุตพริ้นท์
- **แท็บ 3D Models:** แสดง .3dshapes พร้อมรายละเอียดไฟล์ (ขนาด, นามสกุล)

คลิกที่รายการเพื่อดูรายละเอียดแบบขยาย

### Component Search (JLCPCB/EasyEDA)

กดปุ่ม **Component Search** เพื่อค้นหาชิ้นส่วนจาก JLCPCB/EasyEDA:
1. ค้นหาด้วยชื่อชิ้นส่วนหรือ LCSC Part# (เช่น `C2040`)
2. เลือกชิ้นส่วนจากรายการผลลัพธ์
3. กด Import เพื่อนำเข้า symbol, footprint และ 3D model อัตโนมัติ

หรือป้อน LCSC Part# ในช่อง **LCSC Part#** แล้วกด **Import** โดยตรง

---

## CLI Mode

ใช้ import แบบไม่มี GUI:

```bash
cd plugins
python -m KiCadImport -h
```

```text
usage: __main__.py [-h] (--download-folder FOLDER | --download-file FILE | --easyeda ID)
                   --lib-folder FOLDER [--overwrite-if-exists] [--path-variable VAR]
                   [--prefer-step] [--lib-name NAME]

options:
  --download-folder FOLDER   โฟลเดอร์ที่เก็บไฟล์ ZIP
  --download-file FILE       ไฟล์ ZIP ที่ต้องการ import
  --easyeda ID               LCSC Part# เช่น C2040
  --lib-folder FOLDER        โฟลเดอร์ปลายทาง
  --overwrite-if-exists      เขียนทับไฟล์ที่มีอยู่
  --path-variable VAR        ตัวแปร path ($KICAD_3RD_PARTY หรือ $KIPRJMOD)
  --prefer-step              ใช้ STEP แทน WRL สำหรับ 3D model
  --lib-name NAME            ชื่อ library แทนชื่อ source
```

---

## การตั้งค่า

ไฟล์ `plugins/config.ini`:

```ini
[Settings]
src_path = C:\Users\...\Downloads
dest_path = C:\Users\...\KiCad
```

ค่าสามารถแก้ไขผ่าน GUI หรือแก้ไขไฟล์โดยตรง `config.ini` จะถูกเก็บรักษาไว้เมื่ออัปเกรด plugin (ตามที่กำหนดใน `metadata.json`)

---

## การแก้ไขปัญหา

| ปัญหา | สาเหตุ | วิธีแก้ไข |
|-------|--------|-----------|
| `No module named kiutils` | ขาด dependency | `pip install kiutils` หรือ clone submodules |
| `No module named easyeda2kicad` | ขาด dependency | `pip install easyeda2kicad` |
| import ล้มเหลว | รูปแบบ ZIP ไม่รองรับ | ตรวจสอบว่า ZIP มาจากแหล่งที่รองรับ |
| library ไม่แสดงใน KiCad | ยังไม่ได้ตั้งค่า path | ดูหัวข้อการตั้งค่า KiCad |
| IPC API error | ยังไม่ได้เปิด KiCad API | เปิดผ่าน Settings → Plugins |
| `wxPython not found` | ใช้ Python ปกติแทน KiCad Python | ใช้ `run_standalone.bat` หรือกำหนด `KICAD_PYTHON_PATH` |

---

## การพัฒนา

### โครงสร้างโปรเจกต์

```
Import-LIB-KiCad-Plugin/
├── plugins/
│   ├── impart_action.py         # Entrypoint หลักและ event handlers
│   ├── impart_gui.py            # GUI จาก wxFormBuilder (ห้ามแก้ไข)
│   ├── impart_easyeda.py        # EasyEDA/LCSC importer
│   ├── component_search.py      # ค้นหาชิ้นส่วน JLCPCB
│   ├── library_scanner.py       # Scanner สำหรับ Library Browser
│   ├── library_browser.py       # GUI สำหรับ Library Browser
│   ├── single_instance_manager.py # ป้องกัน instance ซ้ำ
│   ├── ConfigHandler/           # จัดการ config.ini
│   ├── FileHandler/             # ตรวจสอบไฟล์ใหม่
│   ├── KiCad_Settings/          # จัดการ KiCad settings files
│   ├── KiCadSettingsPaths/      # ค้นหา KiCad settings path
│   ├── KiCadImport/             # กลไก import หลัก
│   └── kicad_cli/               # Wrapper รอบ kicad-cli
├── metadata.json                # PCM manifest
├── plugin.json                  # KiCad Plugin API manifest
├── run_standalone.bat           # Standalone launcher (Windows)
├── generate_zip.bat             # สร้าง ZIP (Windows)
├── generate_zip.sh              # สร้าง ZIP (Linux/macOS)
└── requirements.txt             # Python dependencies
```

### สร้าง ZIP Package

```bash
# Windows
generate_zip.bat

# Linux/macOS
./generate_zip.sh
```

### Lint และ Type Check

```bash
pip install ruff mypy pyright
ruff check plugins/
mypy plugins/
pyright plugins/
```

---

## เครดิต

- [wexi/impart](https://github.com/wexi/impart) และ [topherbuckley/kicad_remote_import](https://github.com/topherbuckley/kicad_remote_import) — Code ต้นฉบับที่ใช้เป็นพื้นฐานของ GUI
- [uPesy/easyeda2kicad.py](https://github.com/uPesy/easyeda2kicad.py) — EasyEDA import engine (AGPL-3.0)
- [Steffen-W/kiutils](https://github.com/Steffen-W/kiutils) — KiCad library file parser
- ผู้ร่วมพัฒนาและ tester ทุกท่านที่ช่วยแก้ไขข้อบกพร่อง

---

<p align="center">
  <a href="https://github.com/Steffen-W/Import-LIB-KiCad-Plugin/issues/new">
    <img src="https://img.shields.io/badge/รายงานปัญหา-Click_Here-red?logo=github" alt="Report Issue">
  </a>
  <a href="https://ko-fi.com/steffenw1">
    <img src="https://img.shields.io/badge/สนับสนุน-Ko--fi-FF5E5B?logo=kofi" alt="Support on Ko-fi">
  </a>
</p>
