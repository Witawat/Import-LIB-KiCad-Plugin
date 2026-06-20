@echo off
cd /d "%~dp0"

echo ============================================
echo  impart GUI - Standalone Launcher
echo ============================================
echo.

rem Find Python
if exist "C:\Program Files\KiCad\10.0\bin\python.exe" set "PY=C:\Program Files\KiCad\10.0\bin\python.exe" & goto run
if exist "C:\Program Files\KiCad\9.0\bin\python.exe"   set "PY=C:\Program Files\KiCad\9.0\bin\python.exe"   & goto run
if exist "C:\Program Files\KiCad\8.0\bin\python.exe"   set "PY=C:\Program Files\KiCad\8.0\bin\python.exe"   & goto run
if exist "C:\Program Files\KiCad\nightly\bin\python.exe" set "PY=C:\Program Files\KiCad\nightly\bin\python.exe" & goto run
if defined KICAD_PYTHON_PATH if exist "%KICAD_PYTHON_PATH%" set "PY=%KICAD_PYTHON_PATH%" & goto run
where python >nul 2>nul
if not errorlevel 1 set "PY=python" & goto run

echo [ERROR] No Python found.
echo.
echo Options:
echo   - Install KiCad (includes Python + wxPython)
echo   - Set KICAD_PYTHON_PATH=path\to\python.exe
echo   - Add Python to PATH
pause
exit /b 1

:run
echo [OK] Python: %PY%

rem Check wxPython
"%PY%" -c "import wx" 2>nul
if errorlevel 1 (
    echo [ERROR] wxPython not found. Use KiCad's bundled Python.
    pause
    exit /b 1
)

rem Install dependencies if missing
"%PY%" -c "import kiutils" 2>nul
if errorlevel 1 (
    echo [INSTALL] kiutils...
    "%PY%" -m pip install kiutils
)
"%PY%" -c "import easyeda2kicad" 2>nul
if errorlevel 1 (
    echo [INSTALL] easyeda2kicad...
    "%PY%" -m pip install easyeda2kicad
)

echo.
echo [LAUNCH] Starting impartGUI...
echo   - Import ZIP files (Octopart, Samacsys, UltraLibrarian, Snapeda)
echo   - Import EasyEDA / LCSC components
echo   - Library Browser to view imported libraries
echo.

"%PY%" "%~dp0plugins\impart_action.py"
if errorlevel 1 (
    echo.
    echo [ERROR] Plugin exited. Check plugin.log for details.
    pause
)
