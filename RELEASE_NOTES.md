# Release Notes — impartGUI v1.1.0

## What's New

- **Quick Import** — ปุ่ม "Import to KiCad" ใน Component Search Details — import ทันที ไม่ต้องกลับไปหน้าหลัก
- **Link Buttons** — Datasheet / Product Page เป็นปุ่มกดเปิด browser ได้จาก DetailPanel
- **Auto-Resize Columns** — ListCtrl ปรับขนาดคอลัมน์ตามสัดส่วนอัตโนมัติ
- **Smart Text Wrapping** — ข้อความใน cards re-wrap อัตโนมัติเมื่อ image โหลดหรือ resize

## Changelog

- **New:** Actions card รวม Import + Links — Import ซ้าย, Open Datasheet/Product Page ขวา
- **New:** Status bar แสดง "Importing Cxxxxx..." ขณะ import
- **New:** MessageBox แจ้งผล import สำเร็จ
- **New:** `_auto_resize_columns()` กระจายสัดส่วนคอลัมน์ ListCtrl
- **New:** `_rewrap_all_texts()` re-wrap StaticText หลัง image โหลด
- **Fix:** variable shadowing `row` → `btn_row` (AttributeError ใน show_component)
- **Fix:** Name/Description wrapping width ใช้ `wrap_w - 74` ป้องกันล้นกรอบ

## System Requirements

- Windows 10 / 11 (x64)
- KiCad 8.0 / 9.0 / 10.0 หรือไม่ต้องมีก็ได้ (Standalone)
- ต้องมีอินเทอร์เน็ตสำหรับ Component Search และ Preview
