from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import wx
import wx.adv

try:
    from .library_scanner import LibraryScanner
except ImportError:
    from library_scanner import LibraryScanner  # type: ignore[import-not-found,no-redef]

logger = logging.getLogger(__name__)


_COLUMNS: dict[str, list[tuple[str, int, bool]]] = {
    "symbols": [
        ("Library", 150, False),
        ("Symbols", 60, True),
        ("Size (KB)", 80, True),
        ("Source", 100, False),
    ],
    "footprints": [
        ("Library", 150, False),
        ("Footprints", 80, True),
        ("Source", 100, False),
    ],
    "models": [
        ("Library", 150, False),
        ("Files", 60, True),
        ("Formats", 120, False),
    ],
}


class LibraryBrowserDialog(wx.Dialog):
    def __init__(self, parent: wx.Window, scanner: LibraryScanner) -> None:
        super().__init__(
            parent,
            title="Library Browser",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX,
        )

        self.scanner = scanner
        self._scanned: dict[str, list[Any]] = {}

        self.SetSize(750, 500)
        self.Centre()

        root = wx.BoxSizer(wx.VERTICAL)

        header = wx.BoxSizer(wx.HORIZONTAL)
        self._path_label = wx.StaticText(
            self, label=f"Destination: {scanner.dest_path}"
        )
        self._summary_label = wx.StaticText(self, label="")
        self._refresh_btn = wx.Button(self, label="Refresh")
        self._refresh_btn.Bind(wx.EVT_BUTTON, lambda _: self._do_scan())

        header.Add(self._path_label, 1, wx.ALIGN_CENTER_VERTICAL)
        header.Add(self._summary_label, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 8)
        header.Add(self._refresh_btn, 0)
        root.Add(header, 0, wx.EXPAND | wx.ALL, 6)

        self._notebook = wx.Notebook(self)

        self._symbol_list = self._make_list_ctrl("symbols")
        self._fp_list = self._make_list_ctrl("footprints")
        self._model_list = self._make_list_ctrl("models")

        self._notebook.AddPage(self._symbol_list, "Symbols")
        self._notebook.AddPage(self._fp_list, "Footprints")
        self._notebook.AddPage(self._model_list, "3D Models")

        root.Add(self._notebook, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 6)

        btn_row = wx.BoxSizer(wx.HORIZONTAL)
        self._detail_btn = wx.Button(self, label="Show Details")
        self._detail_btn.Bind(wx.EVT_BUTTON, self._on_detail)
        self._detail_btn.Disable()
        close_btn = wx.Button(self, label="Close")
        close_btn.Bind(wx.EVT_BUTTON, lambda _: self.EndModal(wx.ID_OK))
        btn_row.AddStretchSpacer()
        btn_row.Add(self._detail_btn, 0, wx.RIGHT, 6)
        btn_row.Add(close_btn, 0)
        root.Add(btn_row, 0, wx.EXPAND | wx.ALL, 6)

        self.SetSizer(root)
        self._do_scan()

    def _make_list_ctrl(self, kind: str) -> wx.ListCtrl:
        cols = _COLUMNS[kind]
        lc = wx.ListCtrl(
            self._notebook,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SUNKEN,
        )
        for i, (label, width, _) in enumerate(cols):
            lc.InsertColumn(i, label, width=width)
        lc.Bind(wx.EVT_LIST_ITEM_SELECTED, self._on_item_selected)
        lc.Bind(wx.EVT_LIST_ITEM_DESELECTED, lambda _: self._detail_btn.Disable())
        lc.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._on_detail)
        return lc

    def _on_item_selected(self, _: wx.ListEvent) -> None:
        self._detail_btn.Enable()

    def _do_scan(self) -> None:
        self._refresh_btn.Disable()
        self._refresh_btn.SetLabel("Scanning...")
        self._symbol_list.DeleteAllItems()
        self._fp_list.DeleteAllItems()
        self._model_list.DeleteAllItems()
        self._detail_btn.Disable()
        wx.CallAfter(self._background_scan)
        self.Layout()

    def _background_scan(self) -> None:
        try:
            self._scanned = self.scanner.scan_all()
            summary = self.scanner.get_summary()
            wx.CallAfter(self._populate_all, summary)
        except Exception as e:
            logger.exception("Scan failed")
            wx.CallAfter(
                lambda: self._show_scan_error(str(e))
            )

    def _show_scan_error(self, msg: str) -> None:
        wx.MessageBox(f"Scan failed:\n{msg}", "Error", wx.OK | wx.ICON_ERROR)
        self._refresh_btn.Enable()
        self._refresh_btn.SetLabel("Refresh")

    def _populate_all(self, summary: dict[str, int]) -> None:
        self._populate_symbols()
        self._populate_footprints()
        self._populate_models()
        self._summary_label.SetLabel(
            f"{summary['symbol_count']} symbols  |  "
            f"{summary['footprint_count']} footprints  |  "
            f"{summary['model_count']} 3D models"
        )
        self._refresh_btn.Enable()
        self._refresh_btn.SetLabel("Refresh")
        self.Layout()

    def _populate_symbols(self) -> None:
        lc = self._symbol_list
        lc.DeleteAllItems()
        for entry in self._scanned.get("symbols", []):
            idx = lc.InsertItem(lc.GetItemCount(), entry.lib_name)
            lc.SetItem(idx, 1, str(len(entry.symbol_names)))
            lc.SetItem(idx, 2, str(entry.file_size_kb))
            lc.SetItem(idx, 3, self.scanner._detect_source(entry.lib_name))

    def _populate_footprints(self) -> None:
        lc = self._fp_list
        lc.DeleteAllItems()
        for entry in self._scanned.get("footprints", []):
            idx = lc.InsertItem(lc.GetItemCount(), entry.lib_name)
            lc.SetItem(idx, 1, str(entry.file_count))
            lc.SetItem(idx, 2, self.scanner._detect_source(entry.lib_name))

    def _populate_models(self) -> None:
        lc = self._model_list
        lc.DeleteAllItems()
        for entry in self._scanned.get("models", []):
            files = entry.model_files
            exts = sorted({f["extension"] for f in files})
            exts_str = ", ".join(exts) if exts else "-"
            idx = lc.InsertItem(lc.GetItemCount(), entry.lib_name)
            lc.SetItem(idx, 1, str(len(files)))
            lc.SetItem(idx, 2, exts_str)

    def _on_detail(self, _: wx.Event) -> None:
        page = self._notebook.GetSelection()
        kind = ["symbols", "footprints", "models"][page]
        lc = [self._symbol_list, self._fp_list, self._model_list][page]
        sel = lc.GetFirstSelected()
        if sel == wx.NOT_FOUND:
            return
        lib_name = lc.GetItemText(sel, 0)
        entries = self._scanned.get(kind, [])
        entry = next((e for e in entries if e.lib_name == lib_name), None)
        if entry is None:
            return
        dlg = DetailDialog(self, kind, entry)
        dlg.ShowModal()
        dlg.Destroy()


class DetailDialog(wx.Dialog):
    def __init__(self, parent: wx.Window, kind: str, entry: Any) -> None:
        title_map = {
            "symbols": f"Symbol Library: {entry.lib_name}",
            "footprints": f"Footprint Library: {entry.lib_name}",
            "models": f"3D Models: {entry.lib_name}",
        }
        super().__init__(
            parent,
            title=title_map.get(kind, entry.lib_name),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.SetSize(500, 400)
        self.Centre()

        root = wx.BoxSizer(wx.VERTICAL)

        info = wx.BoxSizer(wx.VERTICAL)

        if kind == "symbols":
            info.Add(
                wx.StaticText(
                    self, label=f"File: {entry.file_path.name}"
                ),
                0,
                wx.ALL,
                4,
            )
            info.Add(
                wx.StaticText(
                    self, label=f"Size: {entry.file_size_kb} KB"
                ),
                0,
                wx.ALL,
                4,
            )
            info.Add(
                wx.StaticText(
                    self,
                    label=f"Symbols ({len(entry.symbol_names)}):",
                ),
                0,
                wx.ALL,
                4,
            )
            lb = wx.ListBox(self, choices=sorted(entry.symbol_names))
            info.Add(lb, 1, wx.EXPAND | wx.ALL, 4)

        elif kind == "footprints":
            info.Add(
                wx.StaticText(
                    self, label=f"Directory: {entry.dir_path.name}"
                ),
                0,
                wx.ALL,
                4,
            )
            info.Add(
                wx.StaticText(
                    self,
                    label=f"Footprints ({len(entry.footprint_names)}):",
                ),
                0,
                wx.ALL,
                4,
            )
            lb = wx.ListBox(self, choices=sorted(entry.footprint_names))
            info.Add(lb, 1, wx.EXPAND | wx.ALL, 4)

        else:
            info.Add(
                wx.StaticText(
                    self, label=f"Directory: {entry.dir_path.name}"
                ),
                0,
                wx.ALL,
                4,
            )
            info.Add(
                wx.StaticText(
                    self,
                    label=f"Files ({len(entry.model_files)}):",
                ),
                0,
                wx.ALL,
                4,
            )
            choices = [
                f['name'] for f in entry.model_files
            ]
            lb = wx.ListBox(self, choices=choices)
            info.Add(lb, 1, wx.EXPAND | wx.ALL, 4)

        root.Add(info, 1, wx.EXPAND | wx.ALL, 4)

        btn_row = wx.BoxSizer(wx.HORIZONTAL)
        btn_row.AddStretchSpacer()
        close_btn = wx.Button(self, label="Close")
        close_btn.Bind(wx.EVT_BUTTON, lambda _: self.EndModal(wx.ID_OK))
        btn_row.Add(close_btn, 0)
        root.Add(btn_row, 0, wx.EXPAND | wx.ALL, 6)

        self.SetSizer(root)
