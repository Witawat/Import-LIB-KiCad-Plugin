"""JLCPCB/EasyEDA component search GUI.

Can be used standalone:  python plugins/component_search.py
Or embedded via SearchDialog / SearchPanel in the main plugin.
"""

from __future__ import annotations

import io
import logging
import sys
import threading
import urllib.request
import webbrowser
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import wx
import wx.adv
import wx.html2

# --- make the easyeda2kicad submodule importable ---
current_dir = Path(__file__).resolve().parent
easyeda_submodule = current_dir / "easyeda2kicad"
if easyeda_submodule.exists():
    easyeda_str = str(easyeda_submodule)
    if easyeda_str not in sys.path:
        sys.path.insert(0, easyeda_str)

from easyeda2kicad.easyeda.easyeda_api import EasyedaApi  # noqa: E402

Row = dict[str, Any]

_SEARCH_PAGE_SIZE = 25  # API page size; results are capped at this value
_IMAGE_CACHE_MAX = 50  # max cached product images per session

# (label, field_keys, min_width)  - first matching key wins
COLUMNS: list[tuple[str, list[str], int]] = [
    ("LCSC#", ["lcsc", "componentCode"], 75),
    ("Name", ["name", "componentModelEn"], 140),
    ("Brand", ["brand", "brandNameEn"], 80),
    ("Package", ["package", "packageEnglish"], 90),
    ("Stock", ["stock", "stockCount"], 60),
    ("Type", ["type", "componentLibraryType"], 55),
    ("Price", ["price"], 55),
]

def _pick(row: Row, keys: list[str]) -> str:
    for k in keys:
        v = row.get(k)
        if v is not None and str(v).strip():
            return str(v)
    return ""


@dataclass
class FilterState:
    excluded_brands: set[str] = field(default_factory=set)
    excluded_packages: set[str] = field(default_factory=set)
    excluded_types: set[str] = field(default_factory=set)
    min_stock: int = 0
    min_price: str = ""
    max_price: str = ""

    @property
    def is_active(self) -> bool:
        return bool(
            self.excluded_brands
            or self.excluded_packages
            or self.excluded_types
            or self.min_stock
            or self.min_price
            or self.max_price
        )

    def matches(self, row: Row) -> bool:
        if self.excluded_brands and _pick(row, ["brand", "brandNameEn"]) in self.excluded_brands:
            return False
        if (
            self.excluded_packages
            and _pick(row, ["package", "packageEnglish"]) in self.excluded_packages
        ):
            return False
        if (
            self.excluded_types
            and _pick(row, ["type", "componentLibraryType"]) in self.excluded_types
        ):
            return False
        if self.min_stock:
            try:
                if int(row.get("stock") or 0) < self.min_stock:
                    return False
            except (ValueError, TypeError):
                pass
        price = row.get("price")
        if price is not None:
            try:
                p = float(price)
                if self.min_price and p < float(self.min_price):
                    return False
                if self.max_price and p > float(self.max_price):
                    return False
            except (ValueError, TypeError):
                pass
        return True


class FilterDialog(wx.Dialog):  # type: ignore[misc]
    """Dialog for filtering search results by brand, package, type, stock and price."""

    def __init__(self, parent: wx.Window, results: list[Row], state: FilterState) -> None:
        super().__init__(
            parent, title="Filter Results", style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )

        brands = sorted({v for r in results if (v := _pick(r, ["brand", "brandNameEn"]))})
        packages = sorted({v for r in results if (v := _pick(r, ["package", "packageEnglish"]))})
        types = sorted({v for r in results if (v := _pick(r, ["type", "componentLibraryType"]))})

        main = wx.BoxSizer(wx.VERTICAL)
        lists_row = wx.BoxSizer(wx.HORIZONTAL)

        self._brand_clb = self._clb_group("Brand", brands, state.excluded_brands, lists_row)
        self._package_clb = self._clb_group("Package", packages, state.excluded_packages, lists_row)
        self._type_clb = self._clb_group("Type", types, state.excluded_types, lists_row)

        # Numeric filters
        num_box = wx.StaticBox(self, label="Numeric")
        num_sizer = wx.StaticBoxSizer(num_box, wx.VERTICAL)
        grid = wx.FlexGridSizer(cols=2, vgap=4, hgap=6)
        grid.AddGrowableCol(1)
        self._min_stock = wx.TextCtrl(
            num_box, value=str(state.min_stock) if state.min_stock else "", size=wx.Size(80, -1)
        )
        self._min_price = wx.TextCtrl(num_box, value=state.min_price, size=wx.Size(80, -1))
        self._max_price = wx.TextCtrl(num_box, value=state.max_price, size=wx.Size(80, -1))
        for lbl, ctrl in [
            ("Min Stock:", self._min_stock),
            ("Min Price $:", self._min_price),
            ("Max Price $:", self._max_price),
        ]:
            grid.Add(wx.StaticText(num_box, label=lbl), 0, wx.ALIGN_CENTER_VERTICAL)
            grid.Add(ctrl, 1, wx.EXPAND)
        num_sizer.Add(grid, 0, wx.EXPAND | wx.ALL, 4)
        lists_row.Add(num_sizer, 0, wx.EXPAND)

        main.Add(lists_row, 1, wx.EXPAND | wx.ALL, 6)

        reset_btn = wx.Button(self, label="Reset")
        reset_btn.Bind(wx.EVT_BUTTON, self._on_reset)
        btn_row = wx.BoxSizer(wx.HORIZONTAL)
        btn_row.Add(reset_btn, 0)
        btn_row.AddStretchSpacer()
        btn_row.Add(self.CreateButtonSizer(wx.OK | wx.CANCEL), 0)
        main.Add(btn_row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 6)

        self.SetSizer(main)
        parent_w = parent.GetTopLevelParent().GetSize().width
        self.SetSize(wx.Size(parent_w, 320))

    def _clb_group(
        self, label: str, items: list[str], excluded: set[str], parent_sizer: wx.BoxSizer
    ) -> wx.CheckListBox:
        box = wx.StaticBox(self, label=label)
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        clb = wx.CheckListBox(box, choices=items)
        for i, item in enumerate(items):
            clb.Check(i, item not in excluded)
        # Width: fit longest item (char estimate) up to 200 px, at least 80 px.
        char_w = self.GetCharWidth()
        max_chars = max((len(s) for s in items), default=8)
        w = min(max(max_chars * char_w + 30, 80), 200)
        clb.SetMinSize(wx.Size(w, -1))
        sizer.Add(clb, 1, wx.EXPAND | wx.ALL, 2)
        parent_sizer.Add(sizer, 0, wx.EXPAND | wx.RIGHT, 4)
        return clb

    def _on_reset(self, _: wx.CommandEvent) -> None:
        for clb in (self._brand_clb, self._package_clb, self._type_clb):
            for i in range(clb.GetCount()):
                clb.Check(i, True)
        self._min_stock.SetValue("")
        self._min_price.SetValue("")
        self._max_price.SetValue("")

    def get_state(self) -> FilterState:
        def excluded(clb: wx.CheckListBox) -> set[str]:
            return {clb.GetString(i) for i in range(clb.GetCount()) if not clb.IsChecked(i)}

        def safe_int(ctrl: wx.TextCtrl) -> int:
            # Remove thousands separators (. or ,) then parse as int.
            s = ctrl.GetValue().strip().replace(".", "").replace(",", "")
            try:
                return max(0, int(s))
            except ValueError:
                return 0

        def safe_price(ctrl: wx.TextCtrl) -> str:
            # Normalize German decimal comma to dot.
            return str(ctrl.GetValue().strip().replace(",", "."))

        return FilterState(
            excluded_brands=excluded(self._brand_clb),
            excluded_packages=excluded(self._package_clb),
            excluded_types=excluded(self._type_clb),
            min_stock=safe_int(self._min_stock),
            min_price=safe_price(self._min_price),
            max_price=safe_price(self._max_price),
        )


class DetailPanel(wx.ScrolledWindow):  # type: ignore[misc]
    """Card-based detail panel with categorized sections."""

    _IMG_MAX = 200

    def __init__(self, parent: wx.Window) -> None:
        super().__init__(parent, style=wx.VSCROLL)
        self.SetScrollRate(0, 12)

        self._component_url: str | None = None
        self._viewer_url: str | None = None

        self._img_bmp = wx.StaticBitmap(self)
        self._img_bmp.Hide()
        self._img_bmp.Bind(wx.EVT_LEFT_UP, lambda _: self._open_url(self._component_url))
        self._img_bmp.SetCursor(wx.Cursor(wx.CURSOR_HAND))

        self._outer = wx.BoxSizer(wx.VERTICAL)

        self._placeholder = wx.StaticText(self, label="Select a component to view details")
        f = self._placeholder.GetFont()
        f.SetPointSize(f.GetPointSize() + 2)
        f.SetStyle(wx.FONTSTYLE_ITALIC)
        self._placeholder.SetFont(f)
        self._placeholder.SetForegroundColour(wx.Colour(140, 140, 140))
        self._outer.Add(self._placeholder, 0, wx.ALIGN_CENTER | wx.ALL, 40)

        self._card_boxes: list[wx.StaticBox] = []
        self._card_sizers: list[wx.StaticBoxSizer] = []
        self._viewer_hl: wx.adv.HyperlinkCtrl | None = None

        self._webview = wx.html2.WebView.New(self)
        self._webview.SetMinSize(wx.Size(300, 650))
        self._webview.Hide()

        self.SetSizer(self._outer)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _stock_color(stock_str: str) -> wx.Colour:
        try:
            s = int(stock_str)
            if s >= 1000:
                return wx.Colour(0, 128, 0)
            if s >= 100:
                return wx.Colour(180, 140, 0)
            return wx.Colour(200, 0, 0)
        except (ValueError, TypeError):
            return wx.Colour(0, 0, 0)

    @staticmethod
    def _detach_window(w: wx.Window) -> None:
        if not w or (hasattr(w, 'IsBeingDeleted') and w.IsBeingDeleted()):
            return
        s = w.GetContainingSizer() if hasattr(w, 'GetContainingSizer') else None
        if s:
            s.Detach(w)

    def _make_card(self, title: str) -> tuple[wx.StaticBox, wx.StaticBoxSizer]:
        box = wx.StaticBox(self, label=f"  {title}")
        font = box.GetFont()
        font.MakeBold()
        box.SetFont(font)
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        self._card_sizers.append(sizer)
        self._card_boxes.append(box)
        self._outer.Add(sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 6)
        return box, sizer

    def _add_row(self, parent: wx.Window, card: wx.StaticBoxSizer, label: str, value_widget: wx.Window, /) -> None:
        row = wx.BoxSizer(wx.HORIZONTAL)
        lbl = wx.StaticText(parent, label=f"{label}:")
        lf = lbl.GetFont()
        lf.MakeBold()
        lbl.SetFont(lf)
        lbl.SetMinSize(wx.Size(70, -1))
        row.Add(lbl, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        row.Add(value_widget, 1, wx.ALIGN_CENTER_VERTICAL)
        card.Add(row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 3)

    @staticmethod
    def _make_badge(parent: wx.Window, text: str, bg: wx.Colour, fg: wx.Colour) -> wx.StaticText:
        b = wx.StaticText(parent, label=f"  {text}  ")
        b.SetBackgroundColour(bg)
        b.SetForegroundColour(fg)
        return b

    # ------------------------------------------------------------------
    # Image
    # ------------------------------------------------------------------

    def set_image(self, data: bytes | None) -> None:
        if data:
            try:
                img = wx.Image(io.BytesIO(data))  # pyright: ignore[reportArgumentType, reportCallIssue]
                if img.IsOk():
                    w, h = img.GetWidth(), img.GetHeight()
                    if w > self._IMG_MAX or h > self._IMG_MAX:
                        scale = self._IMG_MAX / max(w, h)
                        new_w = int(w * scale)
                        new_h = int(h * scale)
                        img = img.Scale(new_w, new_h, wx.IMAGE_QUALITY_HIGH)
                    else:
                        new_w, new_h = w, h
                    bmp = wx.Bitmap(img)  # pyright: ignore[reportArgumentType]
                    self._img_bmp.SetBitmap(bmp)
                    self._img_bmp.SetMinSize(wx.Size(new_w, new_h))
                    self._img_bmp.Show()
                    self.Layout()
                    self.FitInside()
                    return
            except Exception as e:
                logging.warning(f"Product image render failed: {e}")
        self._img_bmp.SetMinSize(wx.Size(0, 0))
        self._img_bmp.Hide()
        self.Layout()
        self.FitInside()

    def _open_url(self, url: str | None) -> None:
        if url:
            webbrowser.open(url)

    # ------------------------------------------------------------------
    # Show / Clear
    # ------------------------------------------------------------------

    def show_component(self, row: Row) -> None:
        self._component_url = _pick(row, ["url"]) or None

        # Reparent persistent widgets back to self so they survive box.Destroy()
        self._detach_window(self._img_bmp)
        self._detach_window(self._webview)
        self._img_bmp.Reparent(self)
        self._webview.Reparent(self)
        self._img_bmp.Hide()
        self._webview.Hide()

        # Destroy previous card boxes (cascade-destroys all child widgets inside)
        self._viewer_hl = None
        for box in self._card_boxes:
            if not box or box.IsBeingDeleted():
                continue
            box.Destroy()
        for s in self._card_sizers:
            self._outer.Detach(s)
        self._card_boxes.clear()
        self._card_sizers.clear()

        # Hide placeholder
        self._placeholder.Hide()

        wrap_w = max(180, self.GetClientSize().width - 40)

        # ==============================================================
        # Card: Basic Info (two-column: image left, data right)
        # ==============================================================
        box, card = self._make_card("Basic Info")

        main_row = wx.BoxSizer(wx.HORIZONTAL)

        # Left: product image
        self._img_bmp.Reparent(box)
        main_row.Add(self._img_bmp, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 6)

        # Right: info fields
        right_col = wx.BoxSizer(wx.VERTICAL)

        lcsc_val = _pick(row, ["lcsc", "componentCode"])
        if lcsc_val:
            val = wx.StaticText(box, label=lcsc_val)
            f = val.GetFont(); f.MakeBold(); val.SetFont(f)
            self._add_row(box, right_col, "LCSC#", val)

        name_val = _pick(row, ["name", "componentModelEn"])
        if name_val:
            val = wx.StaticText(box, label=name_val)
            val.Wrap(wrap_w)
            self._add_row(box, right_col, "Name", val)

        brand_val = _pick(row, ["brand", "brandNameEn"])
        type_val = _pick(row, ["type", "componentLibraryType"])
        if brand_val or type_val:
            row_sizer = wx.BoxSizer(wx.HORIZONTAL)
            if brand_val:
                row_sizer.Add(wx.StaticText(box, label=brand_val), 0, wx.ALIGN_CENTER_VERTICAL)
            if type_val:
                if brand_val:
                    row_sizer.Add(wx.StaticText(box, label="  "), 0, wx.ALIGN_CENTER_VERTICAL)
                badge = self._make_badge(box, type_val, wx.Colour(220, 235, 255), wx.Colour(0, 50, 120))
                row_sizer.Add(badge, 0, wx.ALIGN_CENTER_VERTICAL)
            right_col.Add(row_sizer, 0, wx.LEFT | wx.RIGHT | wx.TOP, 3)

        pkg_val = _pick(row, ["package", "packageEnglish"])
        if pkg_val:
            txt = wx.StaticText(box, label=pkg_val)
            txt.Wrap(wrap_w - 74)
            self._add_row(box, right_col, "Package", txt)

        model_val = _pick(row, ["model"])
        if model_val:
            txt = wx.StaticText(box, label=model_val)
            txt.Wrap(wrap_w - 74)
            self._add_row(box, right_col, "Model", txt)

        cat_val = _pick(row, ["category"])
        if cat_val:
            txt = wx.StaticText(box, label=cat_val)
            txt.Wrap(wrap_w - 74)
            self._add_row(box, right_col, "Category", txt)

        desc_val = _pick(row, ["description", "componentDescription"])
        if desc_val:
            txt = wx.StaticText(box, label=desc_val)
            txt.Wrap(wrap_w)
            self._add_row(box, right_col, "Description", txt)

        main_row.Add(right_col, 1, wx.EXPAND)
        card.Add(main_row, 1, wx.EXPAND)

        # ==============================================================
        # Card: Stock & Pricing
        # ==============================================================
        box2, card2 = self._make_card("Stock & Pricing")

        stock_val = _pick(row, ["stock", "stockCount"])
        if stock_val:
            stock_display = stock_val
            try:
                s = int(stock_val)
                stock_display = f"{s:,}"
                if s >= 1000:
                    stock_display += "  (In Stock)"
                elif s >= 100:
                    stock_display += "  (Limited)"
                else:
                    stock_display += "  (Low)"
            except (ValueError, TypeError):
                pass
            val = wx.StaticText(box2, label=stock_display)
            val.SetForegroundColour(self._stock_color(stock_val))
            self._add_row(box2, card2, "Stock", val)

        min_qty = _pick(row, ["min_qty"])
        reel_qty = _pick(row, ["reel_qty"])
        if min_qty:
            self._add_row(box2, card2, "Min Qty", wx.StaticText(box2, label=min_qty))
        if reel_qty:
            self._add_row(box2, card2, "Reel Qty", wx.StaticText(box2, label=reel_qty))

        # Price breaks as formatted list
        price_breaks: list[dict[str, Any]] = row.get("price_breaks") or []
        if price_breaks:
            price_box = wx.BoxSizer(wx.VERTICAL)
            for pb in price_breaks:
                qty = pb.get("qty", "?")
                price = pb.get("price", 0)
                price_str = f"${price:.4f}".rstrip("0").rstrip(".")
                price_box.Add(wx.StaticText(box2, label=f"  {qty}+  {price_str}"), 0)
            self._add_row(box2, card2, "Prices", price_box)

        # ==============================================================
        # Card: Technical Specs
        # ==============================================================
        attributes: list[dict[str, Any]] = row.get("attributes") or []
        if attributes:
            box3, card3 = self._make_card("Technical Specs")
            for attr in attributes:
                name = attr.get("name", "")
                value = attr.get("value", "")
                if name and value:
                    txt = wx.StaticText(box3, label=value)
                    txt.Wrap(wrap_w - 74)  # 70px label + 4px gap
                    self._add_row(box3, card3, name, txt)

        # ==============================================================
        # Card: Links
        # ==============================================================
        link_fields: list[tuple[str, list[str]]] = [
            ("Datasheet", ["datasheet"]),
            ("Product URL", ["url"]),
        ]
        has_links = any(_pick(row, keys) for _, keys in link_fields)
        if has_links:
            box4, card4 = self._make_card("Links")
            for label, keys in link_fields:
                val = _pick(row, keys)
                if val:
                    short = val
                    if len(val) > 65:
                        parsed = urlparse(val)
                        filename = Path(parsed.path).name
                        short = f"{parsed.netloc}/...{filename}" if filename else val[:62] + "..."
                    hl = wx.adv.HyperlinkCtrl(box4, label=short, url=val)
                    self._add_row(box4, card4, label, hl)

        # ==============================================================
        # Card: Previews (proportion=1 to let WebView fill remaining space)
        # ==============================================================
        lcsc_val = _pick(row, ["lcsc", "componentCode"])
        if lcsc_val:
            self._viewer_url = f"https://static.lcsc.com/feassets/pc/html/external-libs/lceda/index.html?{lcsc_val}"

            box5 = wx.StaticBox(self, label="  Previews")
            font = box5.GetFont()
            font.MakeBold()
            box5.SetFont(font)
            card5 = wx.StaticBoxSizer(box5, wx.VERTICAL)
            self._card_boxes.append(box5)
            self._card_sizers.append(card5)
            self._outer.Add(card5, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 6)

            # EasyEDA Web Viewer — fills all remaining vertical space
            self._webview.Reparent(box5)
            card5.Add(self._webview, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 4)

            self._webview.LoadURL(self._viewer_url)
            self._webview.Show()

            # Fallback link: open in external browser
            self._viewer_hl = wx.adv.HyperlinkCtrl(
                box5,
                label="Open in Browser (fallback)",
                url=self._viewer_url,
            )
            hl_row = wx.BoxSizer(wx.HORIZONTAL)
            hl_row.AddStretchSpacer()
            hl_row.Add(self._viewer_hl, 0)
            hl_row.AddStretchSpacer()
            card5.Add(hl_row, 0, wx.EXPAND | wx.BOTTOM, 4)

        self._outer.Layout()
        self.FitInside()
        self.Layout()

    def clear(self) -> None:
        # Reparent persistent widgets back to self before destroying their parent boxes
        self._detach_window(self._img_bmp)
        self._detach_window(self._webview)
        self._img_bmp.Reparent(self)
        self._webview.Reparent(self)
        self._img_bmp.Hide()
        self._webview.Hide()

        for box in self._card_boxes:
            box.Destroy()
        for s in self._card_sizers:
            self._outer.Detach(s)
        self._card_boxes.clear()
        self._card_sizers.clear()
        self._viewer_hl = None

        self._placeholder.Show()
        self.FitInside()
        self.Layout()


class SearchPanel(wx.Panel):  # type: ignore[misc]
    """Self-contained component-search panel - can later be embedded anywhere."""

    def __init__(
        self,
        parent: wx.Window,
        on_select: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self.api = EasyedaApi()
        self._on_select_cb = on_select
        self._all_results: list[Row] = []
        self._results: list[Row] = []
        self._filter_state = FilterState()
        self._sort_col: int = -1
        self._sort_asc: bool = True
        self._search_request_id: int = 0
        self._image_request_id: int = 0
        self._image_cache: OrderedDict[str, bytes] = OrderedDict()
        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = wx.BoxSizer(wx.VERTICAL)

        # ---- search row ----
        search_row = wx.BoxSizer(wx.HORIZONTAL)
        self.search_ctrl = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.search_ctrl.SetHint("Search JLCPCB / EasyEDA …")
        self.btn_search = wx.Button(self, label="Search")
        self.btn_filter = wx.Button(self, label="Filter")
        search_row.Add(self.search_ctrl, 1, wx.EXPAND | wx.RIGHT, 4)
        search_row.Add(self.btn_search, 0, wx.RIGHT, 4)
        search_row.Add(self.btn_filter, 0)
        root.Add(search_row, 0, wx.EXPAND | wx.ALL, 6)

        # ---- splitter: result list (left) / detail panel (right) ----
        splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE | wx.SP_3DSASH)
        splitter.SetMinimumPaneSize(120)

        self.list_ctrl = wx.ListCtrl(
            splitter,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SUNKEN,
        )
        for i, (label, _, width) in enumerate(COLUMNS):
            self.list_ctrl.InsertColumn(i, label, width=width)

        self.detail_panel = DetailPanel(splitter)
        splitter.SplitVertically(self.list_ctrl, self.detail_panel, sashPosition=-360)

        root.Add(splitter, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 6)

        self.list_ctrl.Bind(wx.EVT_SIZE, self._on_list_resize)

        # ---- status line ----
        self.status = wx.StaticText(self, label="")
        root.Add(self.status, 0, wx.LEFT | wx.BOTTOM, 6)

        self.SetSizer(root)

        self.btn_search.Bind(wx.EVT_BUTTON, self._on_search)
        self.search_ctrl.Bind(wx.EVT_TEXT_ENTER, self._on_search)
        self.btn_filter.Bind(wx.EVT_BUTTON, self._on_filter)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self._on_item_selected)
        self.list_ctrl.Bind(wx.EVT_LIST_COL_CLICK, self._on_col_click)

    # ------------------------------------------------------------------
    # Search logic
    # ------------------------------------------------------------------

    def _on_search(self, _: wx.CommandEvent) -> None:
        keyword = self.search_ctrl.GetValue().strip()
        if not keyword:
            return
        self._set_status(f"Searching for '{keyword}' …")
        self.btn_search.Disable()
        self.btn_filter.Disable()
        self.list_ctrl.DeleteAllItems()
        self.detail_panel.clear()
        self._results = []
        self._search_request_id += 1
        req_id = self._search_request_id
        threading.Thread(target=self._do_search, args=(keyword, req_id), daemon=True).start()

    def _do_search(self, keyword: str, req_id: int) -> None:
        try:
            data: dict[str, Any] = self.api.search_jlcpcb_components(
                keyword, page=1, page_size=_SEARCH_PAGE_SIZE
            )
            raw = data.get("result", data.get("results", []))
            results: list[Row] = raw.get("componentList", []) if isinstance(raw, dict) else raw
        except Exception as exc:
            msg = f"Error: {exc}"
            wx.CallAfter(lambda: self._search_done(req_id, [], msg))
            return
        wx.CallAfter(lambda: self._search_done(req_id, results, None))

    def _search_done(self, req_id: int, results: list[Row], error: str | None) -> None:
        if req_id != self._search_request_id:
            return  # superseded by a newer search
        self.btn_search.Enable()
        self.btn_filter.Enable()
        if error:
            self._set_status(error)
            return

        self._all_results = results
        self._filter_state = FilterState()
        self._sort_col = -1
        self._apply_filters()

    def _populate_list(self) -> None:
        self.list_ctrl.DeleteAllItems()
        for row in self._results:
            values = [_pick(row, keys) for (_, keys, _) in COLUMNS]
            idx = self.list_ctrl.InsertItem(self.list_ctrl.GetItemCount(), values[0])
            for col, val in enumerate(values[1:], start=1):
                self.list_ctrl.SetItem(idx, col, val)

    def _on_filter(self, _: wx.CommandEvent) -> None:
        if not self._all_results:
            return
        dlg = FilterDialog(self, self._all_results, self._filter_state)
        if dlg.ShowModal() == wx.ID_OK:
            self._filter_state = dlg.get_state()
            self._apply_filters()
        dlg.Destroy()

    def _apply_filters(self) -> None:
        self._results = [r for r in self._all_results if self._filter_state.matches(r)]
        self._sort_results()
        self._populate_list()
        label = "Filter ●" if self._filter_state.is_active else "Filter"
        self.btn_filter.SetLabel(label)
        total = len(self._all_results)
        shown = len(self._results)
        limit_hint = " (try a more specific search)" if total >= _SEARCH_PAGE_SIZE else ""
        if self._filter_state.is_active:
            self._set_status(
                f"{shown} of {total} result{'s' if total != 1 else ''} shown{limit_hint}."
            )
        else:
            self._set_status(f"{total} result{'s' if total != 1 else ''} found{limit_hint}.")

    def _sort_results(self) -> None:
        if self._sort_col < 0:
            return
        keys = COLUMNS[self._sort_col][1]

        def sort_key(row: Row) -> tuple[int, float | str]:
            val = _pick(row, keys)
            try:
                return (0, float(val))
            except (ValueError, TypeError):
                return (1, val.lower())

        self._results.sort(key=sort_key, reverse=not self._sort_asc)

    def _on_col_click(self, event: wx.ListEvent) -> None:
        col = event.GetColumn()
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True
        self._sort_results()
        self._populate_list()

    # ------------------------------------------------------------------
    # Detail view
    # ------------------------------------------------------------------

    def _on_item_selected(self, event: wx.ListEvent) -> None:
        idx = event.GetIndex()
        if 0 <= idx < len(self._results):
            row = self._results[idx]
            lcsc = _pick(row, ["lcsc", "componentCode"])
            lcsc_url = row.get("url", "")
            self.detail_panel.show_component(row)

            self._image_request_id += 1
            threading.Thread(
                target=self._fetch_image, args=(str(lcsc_url), self._image_request_id), daemon=True
            ).start()

            if self._on_select_cb is not None and lcsc:
                self._on_select_cb(lcsc)

    def _fetch_image(self, lcsc_url: str, req_id: int) -> None:
        if lcsc_url in self._image_cache:
            wx.CallAfter(lambda: self._on_image_ready(req_id, self._image_cache[lcsc_url]))
            return

        data: bytes | None = None
        if lcsc_url:
            try:
                img_url = self.api.get_product_image_url(lcsc_url)
                if img_url:
                    req = urllib.request.Request(img_url, headers=self.api.headers)  # noqa: S310
                    with urllib.request.urlopen(  # noqa: S310
                        req, timeout=10, context=self.api.ssl_context
                    ) as r:
                        data = r.read()
                if data:
                    self._image_cache[lcsc_url] = data
                    if len(self._image_cache) > _IMAGE_CACHE_MAX:
                        self._image_cache.popitem(last=False)  # evict oldest
            except Exception as e:
                logging.debug(f"Image fetch failed for {lcsc_url}: {e}")
        wx.CallAfter(lambda: self._on_image_ready(req_id, data))

    def _on_image_ready(self, req_id: int, data: bytes | None) -> None:
        # Discard result if user has already selected a different component.
        if req_id == self._image_request_id:
            self.detail_panel.set_image(data)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _on_list_resize(self, event: wx.SizeEvent) -> None:
        event.Skip()
        # Stretch the last column to fill any remaining horizontal space.
        total = self.list_ctrl.GetClientSize().width
        used = sum(
            self.list_ctrl.GetColumnWidth(i) for i in range(self.list_ctrl.GetColumnCount() - 1)
        )
        last = self.list_ctrl.GetColumnCount() - 1
        remaining = total - used
        if last >= 0 and remaining > COLUMNS[last][2]:
            self.list_ctrl.SetColumnWidth(last, remaining)

    def _set_status(self, msg: str) -> None:
        self.status.SetLabel(msg)
        self.Layout()

    def get_selected_lcsc(self) -> str | None:
        """Return the LCSC# of the currently selected item, or None."""
        idx = self.list_ctrl.GetFirstSelected()
        if idx == wx.NOT_FOUND:
            return None
        return self.list_ctrl.GetItemText(idx, 0) or None


# ---------------------------------------------------------------------------
# Dialog wrapper – used when embedded in the main plugin GUI
# ---------------------------------------------------------------------------


class SearchDialog(wx.Dialog):  # type: ignore[misc]
    """Wraps SearchPanel in a dialog.

    Parameters
    ----------
    on_select:
        Optional callback called immediately whenever the user clicks a row in
        the result list.  Receives the LCSC# string of the selected component.
    """

    def __init__(
        self,
        parent: wx.Window,
        on_select: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(
            parent,
            title="Component Search",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.panel = SearchPanel(self, on_select=on_select)

        root = wx.BoxSizer(wx.VERTICAL)
        root.Add(self.panel, 1, wx.EXPAND)
        self.SetSizer(root)

        w = parent.GetTopLevelParent().GetSize().width
        self.SetSize(wx.Size(max(w, 800), 600))
        self.Centre()

    def get_lcsc(self) -> str | None:
        return self.panel.get_selected_lcsc()


# ---------------------------------------------------------------------------
# Standalone window (for testing)
# ---------------------------------------------------------------------------


class SearchFrame(wx.Frame):  # type: ignore[misc]
    def __init__(self) -> None:
        super().__init__(
            None,
            title="Component Search (test)",
            size=wx.Size(800, 600),
            style=wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER,
        )
        self.search_panel = SearchPanel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.search_panel, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Centre()


if __name__ == "__main__":
    app = wx.App(False)
    frame = SearchFrame()
    frame.Show()
    app.MainLoop()
