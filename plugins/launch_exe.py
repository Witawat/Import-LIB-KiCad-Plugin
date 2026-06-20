"""KiCad action: launch impartGUI standalone EXE."""
import logging
import subprocess
import sys
import webbrowser
from pathlib import Path


def _log(msg: str) -> None:
    try:
        logging.getLogger("impart_plugin").info(msg)
    except Exception:
        pass


def _find_exe() -> Path | None:
    exe_name = "impartGUI.exe"
    script_dir = Path(__file__).resolve().parent

    candidates: list[Path] = []

    # Relative to this script's location
    candidates.append(script_dir / exe_name)
    candidates.append(script_dir.parent / exe_name)
    candidates.append(script_dir.parent / "dist" / exe_name)

    # PCM install paths (KiCad 8/9/10)
    for version in ("10.0", "9.0", "8.0"):
        pkg_root = (
            Path.home()
            / "AppData"
            / "Roaming"
            / "kicad"
            / version
            / "packages"
            / "com.github.Witawat.impartGUI"
        )
        candidates.append(pkg_root / exe_name)
        candidates.append(pkg_root / "plugins" / exe_name)

    # De-duplicate
    seen: set[str] = set()
    unique: list[Path] = []
    for c in candidates:
        s = str(c.resolve())
        if s not in seen:
            seen.add(s)
            unique.append(c)

    _log(f"Searching for {exe_name} in {len(unique)} locations")
    for path in unique:
        resolved = path.resolve()
        _log(f"  checking: {resolved}")
        if resolved.is_file():
            _log(f"  -> found at {resolved}")
            return resolved

    return None


def launch() -> None:
    exe = _find_exe()
    if exe is not None:
        try:
            _log(f"Launching: {exe}")
            subprocess.Popen([str(exe)], shell=True)
            return
        except Exception as e:
            _log(f"Launch failed: {e}")

    import wx

    app = wx.App() if not wx.GetApp() else None
    msg = (
        f"Could not find impartGUI.exe.\n\n"
        "Make sure the EXE is placed next to the plugin folder.\n"
        "Open the download page now?"
    )
    dlg = wx.MessageDialog(None, msg, "EXE Not Found", wx.YES_NO | wx.ICON_QUESTION)
    if dlg.ShowModal() == wx.ID_YES:
        webbrowser.open(
            "https://github.com/Witawat/Import-LIB-KiCad-Plugin/releases/latest"
        )
    dlg.Destroy()
    if app:
        app.Destroy()


if __name__ == "__main__":
    launch()
