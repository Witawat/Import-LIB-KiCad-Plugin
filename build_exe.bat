@echo off
setlocal
set PYTHON="C:\Program Files\KiCad\10.0\bin\python.exe"
set ROOT=%~dp0
set SCRIPT=%ROOT%plugins\impart_action.py
set DIST=%ROOT%dist

echo Building impartGUI.exe ...

rem Add plugins/ to Python path so PyInstaller finds local packages
set PYTHONPATH=%ROOT%plugins

rem Get Python binary directory for WebView2Loader.dll bundling
for %%i in (%PYTHON%) do set PY_BIN=%%~dpi

%PYTHON% -m PyInstaller --onefile --windowed --name "impartGUI" ^
    --paths "%ROOT%plugins" ^
    --icon "%ROOT%resources\lcsc_favicon.ico" ^
    --add-data "%ROOT%plugins\icon.png;." ^
    --add-data "%ROOT%plugins\config.ini;plugins" ^
    --add-binary "%PY_BIN%WebView2Loader.dll;." ^
    --hidden-import ConfigHandler ^
    --hidden-import FileHandler ^
    --hidden-import impart_gui ^
    --hidden-import KiCad_Settings ^
    --hidden-import KiCadImport ^
    --hidden-import KiCadSettingsPaths ^
    --hidden-import kicad_cli ^
    --hidden-import component_search ^
    --hidden-import easyeda2kicad.easyeda.easyeda_api ^
    --hidden-import kiutils ^
    --distpath "%DIST%" ^
    --clean --noconfirm ^
    "%SCRIPT%"

if %ERRORLEVEL% equ 0 (
    echo.
    echo Done: %DIST%\impartGUI.exe
) else (
    echo.
    echo Build failed.
)
pause
