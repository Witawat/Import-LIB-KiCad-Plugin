"""KiCad action: launch impartGUI standalone EXE."""
import subprocess
import sys
import webbrowser
from pathlib import Path


def launch() -> None:
    exe_name = "impartGUI.exe"
    plugin_dir = Path(__file__).resolve().parent

    candidates = [
        plugin_dir / exe_name,
        plugin_dir.parent / "dist" / exe_name,
        plugin_dir.parent / exe_name,
    ]
    for path in candidates:
        if path.is_file():
            try:
                subprocess.Popen([str(path)], shell=True)
                return
            except Exception:
                pass

    import wx

    app = wx.App() if not wx.GetApp() else None
    dlg = wx.MessageDialog(
        None,
        f"Could not find {exe_name}.\n\n"
        "Download the latest release from GitHub and place it next to the plugin folder.\n"
        "Open download page now?",
        "EXE Not Found",
        wx.YES_NO | wx.ICON_QUESTION,
    )
    if dlg.ShowModal() == wx.ID_YES:
        webbrowser.open(
            "https://github.com/Witawat/Import-LIB-KiCad-Plugin/releases/latest"
        )
    dlg.Destroy()
    if app:
        app.Destroy()


if __name__ == "__main__":
    launch()
