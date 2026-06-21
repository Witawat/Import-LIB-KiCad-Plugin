# คู่มือ API EasyEDA / JLCPCB / LCSC

เอกสารนี้อธิบาย HTTP API ที่ Component Search dialog ใช้ในการค้นหาและแสดงข้อมูลชิ้นส่วน
การเรียก API ทั้งหมดผ่านคลาส `EasyedaApi` จากไลบรารี `easyeda2kicad`
(`easyeda2kicad.easyeda.easyeda_api`) ไม่ต้องใช้ API key

---

## 1. ค้นหาชิ้นส่วน JLCPCB (Shopping Cart API)

ค้นหาชิ้นส่วนจากแคตตาล็อก JLCPCB เป็น endpoint หลักที่ `search_jlcpcb_components()`
เรียกใช้งาน

- **Method:** POST
- **URL:** `https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList`
- **Content-Type:** `application/json`

### ตัวอย่าง payload ที่ส่ง

```json
{
  "keyword": "STM32F103",
  "currentPage": 1,
  "pageSize": 30,
  "componentLibraryType": "base"
}
```

| ฟิลด์ | ชนิด | คำอธิบาย |
|-------|------|----------|
| `keyword` | string | คำค้นหา (LCSC code, ชื่อชิ้นส่วน, ฯลฯ) |
| `currentPage` | int | หน้าที่ต้องการ (เริ่มที่ 1) |
| `pageSize` | int | จำนวนผลลัพธ์ต่อหน้า (ค่าที่ใช้: 30) |
| `componentLibraryType` | string? | `"base"` = Basic, `"expand"` = Extended, ไม่ส่ง = ทั้งหมด |

### โครงสร้าง response

```json
{
  "code": 200,
  "data": {
    "componentPageInfo": {
      "total": 142,
      "list": [ { … }, … ]
    }
  }
}
```

แต่ละ item ใน `list` ถูกแมปดังนี้:

| ฟิลด์ต้นทาง | ฟิลด์ปลายทาง | คำอธิบาย |
|--------------|-------------|----------|
| `componentCode` | `lcsc` | รหัส LCSC (เช่น `C2040`) |
| `componentName` | `name` | ชื่อชิ้นส่วน |
| `componentModelEn` | `model` | หมายเลขรุ่น (ภาษาอังกฤษ) |
| `componentBrandEn` | `brand` | ยี่ห้อ |
| `componentSpecificationEn` | `package` | ชนิดแพคเกจ |
| `componentTypeEn` | `category` | หมวดหมู่ |
| `stockCount` | `stock` | จำนวนสต็อกปัจจุบัน |
| `componentLibraryType` | `type` | `"Basic"` หรือ `"Extended"` |
| `componentPrices` | `price` / `price_breaks` | ราคาแบบแบ่งช่วง |
| `minPurchaseNum` | `min_qty` | จำนวนสั่งซื้อขั้นต่ำ |
| `encapsulationNumber` | `reel_qty` | จำนวนต่อรีล |
| `describe` | `description` | คำอธิบายสั้น |
| `lcscGoodsUrl` | `url` | URL หน้าสินค้า |
| `dataManualUrl` | `datasheet` | URL datasheet |
| `attributes` | `attributes` | สเปคทางเทคนิค (อาเรย์) |
| `componentImageUrl` | `image` | URL รูปสินค้า |

**ที่มา:** `easyeda_api.py` → `search_jlcpcb_components()`

---

## 2. EasyEDA Component API (ข้อมูล CAD)

แปลงรหัส LCSC เป็นข้อมูล CAD ดิบ (symbol JSON, footprint JSON, uuid สำหรับ 3D model)
เรียกโดย `get_info_from_easyeda_api()`

- **Method:** GET
- **URL:** `https://easyeda.com/api/products/{lcsc_id}/components`

### Response

```json
{
  "success": true,
  "result": {
    "dataStr": { … },
    "packageDetail": { … },
    "3dModel": { "uuid": "…" }
  }
}
```

| ฟิลด์ | คำอธิบาย |
|-------|----------|
| `result.dataStr` | JSON ของ symbol (`head.cId` = uuid ใช้ค้นหาชิ้นส่วน) |
| `result.packageDetail` | JSON ของ footprint |
| `result.3dModel.uuid` | UUID สำหรับดึง 3D model |

**หมายเหตุ:** endpoint นี้เป็นส่วนประกอบของ `get_cad_data_of_component()` ซึ่งใช้
ในขั้นตอน import (ไม่ใช่ใน search GUI)

---

## 3. EasyEDA SVG Endpoint (พรีวิว)

ดึง SVG ที่เรนเดอร์ไว้แล้วของ symbol และ footprint ใช้ใน DetailPanel สำหรับ
พรีวิวแบบภาพนิ่ง (สำรองเมื่อ WebView ใช้งานไม่ได้)

- **Method:** GET
- **URL:** `https://easyeda.com/api/products/{lcsc_id}/svgs`

### Response

```json
{
  "result": [
    { "svg": "<svg>…</svg>" },    // symbol unit 1
    { "svg": "<svg>…</svg>" },    // symbol unit N (ถ้ามีหลาย unit)
    { "svg": "<svg>…</svg>" }     // footprint (ตัวสุดท้าย)
  ]
}
```

โค้ดคืนค่า:
- `symbol` = `svg` ของตัวแรก (เมื่อมี 2+ entries)
- `footprint` = `svg` ของตัวสุดท้าย

**ที่มา:** `easyeda_api.py` → `get_svg_from_api()`

---

## 4. พรีวิวผ่าน WebView (LCSC)

แสดง symbol + footprint แบบอินเตอร์แอคทีฟภายใน `wx.html2.WebView`

- **URL:** `https://static.lcsc.com/feassets/pc/html/external-libs/lceda/index.html?{lcsc_val}`
- **lcsc_val:** รหัส LCSC (เช่น `C2040`) ส่งเป็น query parameter

เป็น HTML หน้าเดียวที่ LCSC โฮสต์ไว้ ฝัง EasyEDA viewer ไว้ภายใน
ต้องใช้ WebView2 backend (Edge Chromium) ถึงจะเรนเดอร์ JavaScript ได้ถูกต้อง
ถ้า WebView ตกไปใช้ IE engine พรีวิวจะขึ้นเป็นจอว่าง

**ที่มา:** `component_search.py` → `self._viewer_url` ใน `show_component()`

---

## 5. URL รูปสินค้า

ดึงรูปสินค้าจากหน้า LCSC โดยหา `<meta property="og:image">`

- **Method:** GET
- **URL:** หน้าใดก็ได้บน `https://www.lcsc.com/product-detail/…`
- **การดึงข้อมูล:** `<meta property="og:image" content="https://…">`

สำรอง: JSON-LD `<script type="application/ld+json">` → `image` / `contentUrl` / `thumbnail`

**ที่มา:** `easyeda_api.py` → `get_product_image_url()`

---

## 6. 3D Model Endpoints

| รูปแบบ | URL | Method |
|--------|-----|--------|
| OBJ | `https://modules.easyeda.com/3dmodel/{uuid}` | GET |
| STEP | `https://modules.easyeda.com/qAxj6KHrDKw4blvCG8QJPs7Y/{uuid}` | GET |

คืนค่าข้อมูล 3D model ดิบ ไม่ได้ใช้ใน Component Search GUI แต่ใช้ใน import workflow
เมื่อแปลงชิ้นส่วนเป็น KiCad format

**ที่มา:** `easyeda_api.py` → `get_raw_3d_model_obj()`, `get_step_3d_model()`

---

## 7. EasyEDA Pro v2 API (แปลง LCSC → UUID แบบทีละหลายตัว)

แปลงรหัส LCSC หลายตัวเป็น component UUID ในการเรียกครั้งเดียว

- **Method:** POST
- **URL:** `https://easyeda.com/api/components/searchByNumbers`
- **Content-Type:** `application/x-www-form-urlencoded; charset=UTF-8`
- **Body:** `numbers=["C2040","C20197"]` (JSON-stringified array, form-encoded)

**หมายเหตุ:** ใช้ภายใน import workflow ไม่ได้ใช้ใน search dialog

**ที่มา:** `easyeda_api.py` → `search_v2_component_uuids_by_lcsc()`

---

## 8. Headers และ SSL

ทุก request ใช้ headers ร่วมกันดังนี้:

```
Accept-Encoding: gzip, deflate
Accept: application/json, text/javascript, */*; q=0.01
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 …
Referer: https://easyeda.com/
```

**การคลาย compression:** ถ้า byte ดิบขึ้นต้นด้วย `\x1f\x8b` (gzip magic)
โค้ดจะใช้ `gzip.decompress()` ก่อนถอดรหัส

**SSL context:**
1. macOS → ลองใช้ certifi ที่มาพร้อม KiCad (`cacert.pem`)
2. ทุกแพลตฟอร์ม → ลองใช้ `certifi` pip package ถ้ามี
3. สำรอง → ใช้ system default SSL context

**ที่มา:** `easyeda_api.py` → `__init__()`, `_decode_response()`, `_create_ssl_context()`

---

## 9. Caching

เมื่อ `use_cache=True` ระบบจะบันทึก response ของ API ไว้เป็นไฟล์ในโฟลเดอร์
`.easyeda_cache/` ใน working directory ปัจจุบัน ไฟล์ JSON จะจัดรูปแบบให้อ่านง่าย
(indent=2)

---

## 10. การจัดการข้อผิดพลาด

- Network error (`URLError`) → log + คืนค่า `{}` หรือ `{"total": 0, "results": []}`
- JSON decode error → log + คืนค่า fallback
- Timeout: 30 วินาที สำหรับ CAD data / 3D model, 15 วินาที สำหรับ search / SVG / รูปสินค้า
- Hostname ไม่ถูกต้องใน `get_product_image_url()` → คืนค่า `None` โดยไม่แจ้งเตือน

---

## ไฟล์ที่เกี่ยวข้อง

| ไฟล์ | บทบาท |
|------|--------|
| `plugins/component_search.py` | GUI frontend, เรียก `search_jlcpcb_components()`, `get_svg_from_api()`, `get_product_image_url()` |
| `easyeda2kicad/easyeda/easyeda_api.py` | คลาส `EasyedaApi` — wrapper ทุก endpoint (git submodule) |
| `plugins/impart_easyeda.py` | Import workflow, ใช้ `get_cad_data_of_component()`, `search_v2_component_uuids_by_lcsc()` |

---

## หมายเหตุ (ค้นหาแบบไม่ระบุคำค้น)

JLCPCB search API ยังทำงานได้เมื่อ **ไม่ใส่ keyword** — จะคืนค่าชิ้นส่วนทั้งหมด
แบบแบ่งหน้า Component Search dialog ไม่ได้ใช้ path นี้ (กำหนดขั้นต่ำ 2 ตัวอักษร)
แต่สามารถใช้สำหรับเรียกดูแคตตาล็อกทั้งหมดได้
