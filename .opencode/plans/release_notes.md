# Release Notes — impartGUI v1.1.0

> สร้าง Release ที่: https://github.com/Witawat/Import-LIB-KiCad-Plugin/releases/new
> อัปโหลด: `dist\impartGUI.exe`

---

## What's New

- **Quick Import** — ปุ่ม "Import to KiCad" ใน Component Search Details — import ทันที ไม่ต้องกลับไปหน้าหลัก
- **Link Buttons** — Datasheet / Product Page เป็นปุ่มกดเปิด browser ได้จาก DetailPanel Actions card
- **Auto-Resize Columns** — ListCtrl ปรับขนาดคอลัมน์ตามสัดส่วนอัตโนมัติเมื่อ resize
- **Smart Text Wrapping** — ข้อความใน DetailPanel re-wrap อัตโนมัติเมื่อ image โหลดหรือ resize หน้าต่าง

## Changelog

- **New:** Actions card เรียงแนวนอน Import อยู่ซ้าย, Open Datasheet/Product Page อยู่ขวา
- **New:** Status bar แสดง "Importing Cxxxxx..." ขณะ import
- **New:** MessageBox แจ้งผล import สำเร็จ/ล้มเหลว
- **New:** `_auto_resize_columns()` — กระจาย extra space ตามสัดส่วน min_width
- **New:** `_rewrap_all_texts()` + `_walk_and_wrap()` — recursive re-wrap StaticText
- **Fix:** variable shadowing (`row` → `btn_row`) ทำให้ AttributeError ใน `show_component`
- **Fix:** Name/Description wrapping width (ใช้ `-74` ป้องกันล้นกรอบตอนมี image)

## System Requirements

- Windows 10 / 11 (x64)
- KiCad 8.0 / 9.0 / 10.0 หรือไม่ต้องมีก็ได้ (Standalone)
- ต้องมีอินเทอร์เน็ตสำหรับ Component Search และ Preview
