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

    # KiCad user plugins directory (manual install)
    for version in ("10.0", "9.0", "8.0"):
        scripting = (
            Path.home()
            / "AppData"
            / "Roaming"
            / "kicad"
            / version
            / "scripting"
            / "plugins"
        )
        candidates.append(scripting / exe_name)
        candidates.append(scripting.parent / exe_name)

    # Alternate PCM path under Documents
    for version in ("10.0", "9.0", "8.0"):
        alt = Path.home() / "Documents" / "KiCad" / version / "packages" / "com.github.Witawat.impartGUI"
        candidates.append(alt / exe_name)
        candidates.append(alt / "plugins" / exe_name)

    # De-duplicate
    seen: set[str] = set()
    unique: list[Path] = []
    for c in candidates:
        s = str(c.resolve())
        if s not in seen:
            seen.add(s)
            unique.append(c)

    searched = ""
    _log(f"Searching for {exe_name} in {len(unique)} locations")
    for path in unique:
        resolved = path.resolve()
        _log(f"  checking: {resolved}")
        searched += f"\n  {resolved}"
        if resolved.is_file():
            _log(f"  -> found at {resolved}")
            return resolved

    _log("EXE not found")
    return None


def _debug_paths() -> str:
    lines = [f"__file__: {__file__}"]
    lines.append(f"cwd: {Path.cwd()}")
    for v in ("10.0", "9.0", "8.0"):
        pkg = Path.home() / "AppData" / "Roaming" / "kicad" / v / "packages" / "com.github.Witawat.impartGUI" / "impartGUI.exe"
        lines.append(f"PCM {v}: {'EXISTS' if pkg.is_file() else 'missing'}")
    return "\n".join(lines)


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
        "Download from GitHub Releases?\n\n"
        f"-- debug --\n{_debug_paths()}"
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
