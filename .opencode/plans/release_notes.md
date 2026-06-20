# Release Notes — impartGUI v1.0.0

> สร้าง Release ที่: https://github.com/Witawat/Import-LIB-KiCad-Plugin/releases/new
> อัปโหลด: `dist\impartGUI.exe`

---

## What's New

- **Component Search** — ค้นหาชิ้นส่วนจาก JLCPCB / EasyEDA / LCSC ในตัว
- **Real-time Preview** — ดู symbol และ footprint ของชิ้นส่วนผ่าน EasyEDA Web Viewer
- **Multi-format Import** — รองรับ ZIP (Octopart, Samacsys, UltraLibrarian, Snapeda), EasyEDA, LCSC
- **Library Browser** — ดูไลบรารีที่ import แล้ว
- **Single-file EXE** — ใช้งานได้ทันทีไม่ต้องติดตั้ง Python หรือ KiCad (ใช้ Python 11 + wxPython 4.2.2)

## Changelog

- **Fix:** Bundle `WebView2Loader.dll` กับ PyInstaller build — แก้ปัญหา WebView Preview แสดงเฉพาะกรอบเปล่า ไม่มี symbol/footprint (IE fallback)
- **Fix:** ปรับปรุงการเขียนการตั้งค่าคงอยู่ (`debug_log` toggle ใน `config.ini`)
- **Fix:** แก้ kiutils encoding issue
- **New:** ปรับปรุง DetailPanel เป็น Card-based layout
- **New:** เปลี่ยนจาก SVG renderer เป็น `wx.html2.WebView` สำหรับพรีวิวชิ้นส่วน (EasyEDA viewer)
- **New:** รันแบบ GUI ธรรมดาโดยไม่ต้องเปิด KiCad

## EXE Checksum

```
File:      impartGUI.exe
Size:      57.7 MB
SHA256:    1b235522a764b96f534fe8132d30932cae7d1736bfb4ac323950538b8e0c74ba
```

## System Requirements

- Windows 10 / 11 (x64)
- ไม่ต้องติดตั้ง KiCad หรือ Python
- ต้องมีอินเทอร์เน็ตสำหรับ Component Search และ Preview
