@echo off
setlocal EnableDelayedExpansion
title GTU Proliz Ders Kayit Botu
color 0b

echo ========================================================
echo       GTU PROLIZ DERS KAYIT BOTU - BASLATILIYOR
echo ========================================================
echo.

set "PY_CMD="

:: 1. Standart Windows Python Launcher (py -3) kontrolu
py -3 -c "import sys" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    py -3 -m pip --version >nul 2>&1
    if !ERRORLEVEL% EQU 0 (
        set PY_CMD=py -3
        goto :FOUND_PY
    )
)

:: 2. AppData altindaki resmi Windows Python kurulumu kontrolu
for /d %%i in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
    if exist "%%i\python.exe" (
        "%%i\python.exe" -m pip --version >nul 2>&1
        if !ERRORLEVEL! EQU 0 (
            set PY_CMD="%%i\python.exe"
            goto :FOUND_PY
        )
    )
)

:: 3. Program Files altindaki Python kontrolu
for /d %%i in ("%ProgramFiles%\Python3*") do (
    if exist "%%i\python.exe" (
        "%%i\python.exe" -m pip --version >nul 2>&1
        if !ERRORLEVEL! EQU 0 (
            set PY_CMD="%%i\python.exe"
            goto :FOUND_PY
        )
    )
)

:: 4. C:\Python3* kontrolu
for /d %%i in (C:\Python3*) do (
    if exist "%%i\python.exe" (
        "%%i\python.exe" -m pip --version >nul 2>&1
        if !ERRORLEVEL! EQU 0 (
            set PY_CMD="%%i\python.exe"
            goto :FOUND_PY
        )
    )
)

:: 5. Sistemdeki mevcut py veya python
py -3 -c "import sys" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PY_CMD=py -3
) else (
    set PY_CMD=python
)

:FOUND_PY
echo [*] Secilen Python motoru: %PY_CMD%
echo.

:: Pip modulu kontrolu ve otomatik onarimi
%PY_CMD% -m pip --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [!] 'pip' modulu eksik tespit edildi! Otomatik cozumler deneniyor...
    
    :: Yontem A: ensurepip ile pip yukle
    %PY_CMD% -m ensurepip --default-pip >nul 2>&1
    
    :: Yontem B: Eger MSYS2 / MinGW ortami ise pacman ile pip ve selenium yukle
    if exist "C:\msys64\usr\bin\pacman.exe" (
        echo [*] MSYS2 ortami tespit edildi, pacman ile pip ve selenium kuruluyor...
        C:\msys64\usr\bin\pacman.exe -S --noconfirm mingw-w64-x86_64-python-pip mingw-w64-x86_64-python-selenium 2>nul
    )
    
    :: Yontem C: get-pip.py ile pip kur
    %PY_CMD% -m pip --version >nul 2>&1
    if !ERRORLEVEL! NEQ 0 (
        echo [*] get-pip.py indiriliyor ve kuruluyor...
        curl -sS https://bootstrap.pypa.io/get-pip.py -o "%TEMP%\get-pip.py" 2>nul
        if exist "%TEMP%\get-pip.py" (
            %PY_CMD% "%TEMP%\get-pip.py" >nul 2>&1
            del "%TEMP%\get-pip.py" 2>nul
        )
    )
)

:: Selenium kontrolu ve otomatik kurulumu
%PY_CMD% -c "import selenium" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] Selenium kutuphanesi eksik tespit edildi!
    echo [*] Selenium otomatik olarak kuruluyor, lutfen bekleyin...
    echo.
    %PY_CMD% -m pip install selenium
    if !ERRORLEVEL! NEQ 0 (
        if exist "C:\msys64\usr\bin\pacman.exe" (
            C:\msys64\usr\bin\pacman.exe -S --noconfirm mingw-w64-x86_64-python-selenium
        )
    )
    %PY_CMD% -c "import selenium" >nul 2>&1
    if !ERRORLEVEL! NEQ 0 (
        echo.
        echo [X] Selenium otomatik yuklenemedi.
        echo Lutfen standart Python ortaminda su komutu calistirin: pip install selenium
        echo.
        pause
        exit /b
    )
    echo.
    echo [OK] Selenium basariyla kuruldu!
    echo.
)

echo [*] Bot Arayuzu (GUI) baslatiliyor...
echo.
%PY_CMD% main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] Bot beklenmeyen bir hata ile kapandi.
    echo [!] Detayli hata kayitlari icin 'logs' klasorune bakabilirsiniz.
    pause
)
