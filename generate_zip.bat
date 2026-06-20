@echo off
cd /d "%~dp0"

set "BUILD_DIR=%TEMP%\impart_build"
set "ZIP_OUT=%~dp0Import-LIB-KiCad-Plugin.zip"

rem Clean old build
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
if exist "%ZIP_OUT%" del "%ZIP_OUT%"

mkdir "%BUILD_DIR%"
mkdir "%BUILD_DIR%\plugins"

echo ============================================
echo  Import-LIB-KiCad-Plugin - Package Builder
echo ============================================
echo.

rem --- Copy metadata and resources ---
echo [1/8] metadata.json
copy "metadata.json" "%BUILD_DIR%\" >nul

if exist "resources" (
    echo [1/8] resources\
    xcopy /e /i /q "resources" "%BUILD_DIR%\resources\" >nul
)

rem --- Copy plugin Python files ---
echo [2/8] plugins\*.py
copy "plugins\*.py" "%BUILD_DIR%\plugins\" >nul

echo [2/8] plugins\plugin.json
if exist "plugins\plugin.json" copy "plugins\plugin.json" "%BUILD_DIR%\plugins\" >nul

echo [2/8] plugins\config.ini
if exist "plugins\config.ini" copy "plugins\config.ini" "%BUILD_DIR%\plugins\" >nul

echo [2/8] plugins\requirements.txt
copy "plugins\requirements.txt" "%BUILD_DIR%\plugins\" >nul

echo [2/8] plugins\icon.png
if exist "plugins\icon.png" copy "plugins\icon.png" "%BUILD_DIR%\plugins\" >nul

rem --- Copy plugin subdirectories (excluding git submodules) ---
echo [3/8] plugin modules
for %%d in (ConfigHandler FileHandler KiCad_Settings KiCadSettingsPaths KiCadImport kicad_cli) do (
    if exist "plugins\%%d" (
        xcopy /e /i /q "plugins\%%d" "%BUILD_DIR%\plugins\%%d\" >nul
    )
)

rem --- Locate KiCad Python site-packages ---
set "KICAD_SITE_PKG="
for %%p in (
    "C:\Program Files\KiCad\10.0\bin"
    "C:\Program Files\KiCad\9.0\bin"
    "C:\Program Files\KiCad\8.0\bin"
    "C:\Program Files\KiCad\nightly\bin"
) do (
    if not defined KICAD_SITE_PKG if exist "%%~p\python.exe" (
        for /f "delims=" %%v in ('"%%~p\python.exe" -c "import site; print(site.getsitepackages()[0])" 2^>nul') do set "KICAD_SITE_PKG=%%v"
    )
)

if not defined KICAD_SITE_PKG (
    rem Fallback: common site-packages paths
    if exist "D:\XSoFTz\Documents\KiCad\10.0\3rdparty\Python311\site-packages\" set "KICAD_SITE_PKG=D:\XSoFTz\Documents\KiCad\10.0\3rdparty\Python311\site-packages"
)

rem --- Vendor kiutils ---
echo [4/8] kiutils
if exist "plugins\kiutils\src\kiutils\__init__.py" (
    rem Use local submodule
    mkdir "%BUILD_DIR%\plugins\kiutils\src"
    xcopy /e /i /q "plugins\kiutils\src\kiutils" "%BUILD_DIR%\plugins\kiutils\src\kiutils\" >nul
    echo   from local submodule
) else if defined KICAD_SITE_PKG (
    rem Vendor from KiCad site-packages
    mkdir "%BUILD_DIR%\plugins\kiutils\src"
    robocopy "%KICAD_SITE_PKG%\kiutils" "%BUILD_DIR%\plugins\kiutils\src\kiutils" /E /NDL /NJH /NJS >nul
    echo   from %KICAD_SITE_PKG%
) else (
    echo   [SKIP] kiutils not available - add manually or install via pip
)

rem --- Vendor easyeda2kicad ---
echo [5/8] easyeda2kicad
if exist "plugins\easyeda2kicad\easyeda2kicad\__init__.py" (
    rem Use local submodule
    mkdir "%BUILD_DIR%\plugins\easyeda2kicad"
    xcopy /e /i /q "plugins\easyeda2kicad\easyeda2kicad" "%BUILD_DIR%\plugins\easyeda2kicad\easyeda2kicad\" >nul
    echo   from local submodule
) else if defined KICAD_SITE_PKG (
    rem Vendor from KiCad site-packages
    mkdir "%BUILD_DIR%\plugins\easyeda2kicad"
    robocopy "%KICAD_SITE_PKG%\easyeda2kicad" "%BUILD_DIR%\plugins\easyeda2kicad\easyeda2kicad" /E /NDL /NJH /NJS >nul
    echo   from %KICAD_SITE_PKG%
) else (
    echo   [SKIP] easyeda2kicad not available - add manually or install via pip
)

rem --- Include standalone launcher ---
echo [6/8] run_standalone.bat
if exist "run_standalone.bat" copy "run_standalone.bat" "%BUILD_DIR%\" >nul

rem --- Include standalone EXE (if built) ---
if exist "dist\impartGUI.exe" (
    echo [6/8] impartGUI.exe
    copy "dist\impartGUI.exe" "%BUILD_DIR%\" >nul
)

rem --- Cleanup unwanted files ---
echo [7/9] cleanup
for /d /r "%BUILD_DIR%" %%d in (__pycache__) do if exist "%%d" rmdir /s /q "%%d" 2>nul
del /s /q "%BUILD_DIR%\*.pyc" 2>nul
del /s /q "%BUILD_DIR%\*.log" 2>nul
del /s /q "%BUILD_DIR%\*.fbp" 2>nul
del /s /q "%BUILD_DIR%\*.svg" 2>nul

rem --- Create ZIP ---
echo [8/9] creating ZIP
echo.

where powershell >nul 2>nul
if errorlevel 1 (
    echo [ERROR] PowerShell required for ZIP creation.
    pause
    exit /b 1
)

powershell -command "Add-Type -AssemblyName System.IO.Compression.FileSystem; [System.IO.Compression.ZipFile]::CreateFromDirectory('%BUILD_DIR%', '%ZIP_OUT%')" 2>&1

if errorlevel 1 (
    echo [ERROR] ZIP creation failed.
    pause
    exit /b 1
)

rem --- Show result ---
set "SIZE=0"
for %%f in ("%ZIP_OUT%") do set "SIZE=%%~zf"
set /a "SIZE_KB=%SIZE%/1024"

echo.
echo [OK] Package created: %ZIP_OUT%
echo [OK] Size: %SIZE_KB% KB
echo.
echo You can now install via KiCad:
echo   Tools -^> Plugin and Content Manager
echo   -^> Install from File...
echo   -^> Select Import-LIB-KiCad-Plugin.zip
echo.

rem Cleanup
rmdir /s /q "%BUILD_DIR%" 2>nul

pause
