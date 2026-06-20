# EasyEDA / JLCPCB / LCSC API Reference

This document describes the HTTP APIs used by the Component Search dialog to query and display
electronic components.  All calls go through the `EasyedaApi` class from the
`easyeda2kicad` library (`easyeda2kicad.easyeda.easyeda_api`).  No API key is required.

---

## 1. JLCPCB Component Search (Shopping Cart API)

Search the JLCPCB parts catalogue.  This is the primary search endpoint called by
`search_jlcpcb_components()`.

- **Method:** POST
- **URL:** `https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList`
- **Content-Type:** `application/json`

### Request payload

```json
{
  "keyword": "STM32F103",
  "currentPage": 1,
  "pageSize": 30,
  "componentLibraryType": "base"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `keyword` | string | Search term (LCSC code, part name, etc.) |
| `currentPage` | int | Page number (1-based) |
| `pageSize` | int | Results per page (used: 30) |
| `componentLibraryType` | string? | `"base"` = Basic, `"expand"` = Extended, omit = all |

### Response structure

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

Each item in `list` is mapped to these fields:

| Source field | Mapped key | Description |
|--------------|-----------|-------------|
| `componentCode` | `lcsc` | LCSC part number (e.g. `C2040`) |
| `componentName` | `name` | Component name |
| `componentModelEn` | `model` | English model number |
| `componentBrandEn` | `brand` | Brand name |
| `componentSpecificationEn` | `package` | Package type |
| `componentTypeEn` | `category` | Component category |
| `stockCount` | `stock` | Current stock count |
| `componentLibraryType` | `type` | `"Basic"` or `"Extended"` |
| `componentPrices` | `price` / `price_breaks` | Pricing tiers |
| `minPurchaseNum` | `min_qty` | Minimum order qty |
| `encapsulationNumber` | `reel_qty` | Reel quantity |
| `describe` | `description` | Short description |
| `lcscGoodsUrl` | `url` | Product page URL |
| `dataManualUrl` | `datasheet` | Datasheet URL |
| `attributes` | `attributes` | Technical specs array |
| `componentImageUrl` | `image` | Product image URL |

**Source:** `easyeda_api.py` → `search_jlcpcb_components()`

---

## 2. EasyEDA Component API (CAD data)

Resolve an LCSC number to the raw CAD data (symbol json, footprint json, 3D model uuid).
Called by `get_info_from_easyeda_api()`.

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

| Field | Description |
|-------|-------------|
| `result.dataStr` | Symbol JSON (`head.cId` = uuid for parts search) |
| `result.packageDetail` | Footprint JSON |
| `result.3dModel.uuid` | UUID to fetch 3D model |

**Note:** This endpoint is the building block of `get_cad_data_of_component()` which
is used by the import workflow (not the search GUI).

---

## 3. EasyEDA SVG Endpoint (Preview)

Fetch pre-rendered SVG strings for symbol and footprint.  Used by the DetailPanel
for static image previews (fallback when WebView is unavailable).

- **Method:** GET
- **URL:** `https://easyeda.com/api/products/{lcsc_id}/svgs`

### Response

```json
{
  "result": [
    { "svg": "<svg>…</svg>" },    // symbol unit 1
    { "svg": "<svg>…</svg>" },    // symbol unit N (if multi-unit)
    { "svg": "<svg>…</svg>" }     // footprint (last entry)
  ]
}
```

The code returns:
- `symbol` = first entry's `svg` (when there are 2+ entries)
- `footprint` = last entry's `svg`

**Source:** `easyeda_api.py` → `get_svg_from_api()`

---

## 4. LCSC WebView Preview

Display symbol + footprint interactively inside a `wx.html2.WebView` control.

- **URL:** `https://static.lcsc.com/feassets/pc/html/external-libs/lceda/index.html?{lcsc_val}`
- **lcsc_val:** The LCSC number (e.g. `C2040`) passed as a query parameter.

This is a static HTML page hosted by LCSC that embeds the EasyEDA viewer.  It requires
a WebView2 backend (Edge Chromium) to render JavaScript correctly.  If the WebView
falls back to the IE engine the preview will be blank.

**Source:** `component_search.py:539`

---

## 5. Product Image URL

Scrape the LCSC product page for the product image (`og:image` meta tag).

- **Method:** GET
- **URL:** Any `https://www.lcsc.com/product-detail/…` page
- **Extraction:** `<meta property="og:image" content="https://…">`

Fallback: JSON-LD `<script type="application/ld+json">` → `image` / `contentUrl` / `thumbnail`.

**Source:** `easyeda_api.py` → `get_product_image_url()`

---

## 6. 3D Model Endpoints

| Format | URL | Method |
|--------|-----|--------|
| OBJ | `https://modules.easyeda.com/3dmodel/{uuid}` | GET |
| STEP | `https://modules.easyeda.com/qAxj6KHrDKw4blvCG8QJPs7Y/{uuid}` | GET |

These return the raw 3D model data.  Not used by Component Search GUI but used by the
main import workflow when converting a component to KiCad format.

**Source:** `easyeda_api.py` → `get_raw_3d_model_obj()`, `get_step_3d_model()`

---

## 7. EasyEDA Pro v2 API (batch LCSC → UUID resolution)

Resolve multiple LCSC numbers to component UUIDs in one request.

- **Method:** POST
- **URL:** `https://easyeda.com/api/components/searchByNumbers`
- **Content-Type:** `application/x-www-form-urlencoded; charset=UTF-8`
- **Body:** `numbers=["C2040","C20197"]` (JSON-stringified array, form-encoded)

**Note:** Used internally by the import workflow, not by the search dialog.

**Source:** `easyeda_api.py` → `search_v2_component_uuids_by_lcsc()`

---

## 8. Headers & SSL

All requests share these headers:

```
Accept-Encoding: gzip, deflate
Accept: application/json, text/javascript, */*; q=0.01
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 …
Referer: https://easyeda.com/
```

Response decompression: if the raw bytes start with `\x1f\x8b` (gzip magic), the
code uses `gzip.decompress()` before decoding.

SSL context:
1. macOS → tries KiCad's bundled certifi (`cacert.pem`)
2. All platforms → tries `certifi` pip package if available
3. Fallback → system default SSL context

**Source:** `easyeda_api.py` → `__init__()`, `_decode_response()`, `_create_ssl_context()`

---

## 9. Caching

When `use_cache=True`, API responses are saved as files under `.easyeda_cache/`
in the current working directory.  JSON files are pretty-printed (indent=2).

---

## 10. Error Handling

- Network errors (`URLError`) → log + return `{}` or `{"total": 0, "results": []}`
- JSON decode errors → log + return fallback
- Timeouts: 30 s for CAD data / 3D models, 15 s for search / SVG / product image
- Invalid hostname in `get_product_image_url()` → silently return `None`

---

## Related Files

| File | Role |
|------|------|
| `plugins/component_search.py` | GUI frontend, calls `search_jlcpcb_components()`, `get_svg_from_api()`, `get_product_image_url()` |
| `easyeda2kicad/easyeda/easyeda_api.py` | `EasyedaApi` class — all endpoint wrappers (git submodule) |
| `plugins/impart_easyeda.py` | Import workflow, uses `get_cad_data_of_component()`, `search_v2_component_uuids_by_lcsc()` |

---

## Test (no-keyword) notes

The JLCPCB search API also works with an **empty keyword** — it returns every
component paginated.  The Component Search dialog does not use this path (minimum
query is 2 characters), but it is available for bulk-catalogue browsing.
