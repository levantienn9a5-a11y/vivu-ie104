@echo off
chcp 65001 >nul
cd /d "%~dp0"
title ViVu - Khoi dong website
if not exist "server.py" goto missing_files
if not exist "public\index.html" goto missing_files
if not exist "public\app.js" goto missing_files
if not exist "public\style.css" goto missing_files
if not exist "public\trip-filters.js" goto missing_files
echo Dang khoi dong ViVu...
echo Giu cua so nay mo trong khi su dung website.
echo.
if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
 "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
 if not errorlevel 1 goto bundled
)
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
if not errorlevel 1 goto launcher
python -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
if not errorlevel 1 goto python

echo [THIEU PYTHON] Can cai Python 3.10 tro len tren may nay.
echo Tai tai: https://www.python.org/downloads/windows/
echo Khi cai dat, bat tuy chon Add Python to PATH neu co.
echo Cai xong, dong cua so nay va mo lai CHAY-WEB.bat.
goto done
:bundled
"%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -X utf8 server.py --open-browser
goto result
:launcher
py -3 -X utf8 server.py --open-browser
goto result
:python
python -X utf8 server.py --open-browser
goto result
:result
if errorlevel 1 (
 echo.
 echo [KHONG KHOI DONG DUOC] Xem thong bao loi o phia tren.
 echo Neu cong 8000 dang ban: dung lenh py -3 server.py --port 8001 --open-browser
)
goto done
:missing_files
echo [THIEU MA NGUON] Khong the chay chi bang file CHAY-WEB.bat.
echo Hay giai nen TOAN BO goi ViVu, sau do mo file nay trong thu muc da giai nen.
echo Can co server.py va thu muc public nam canh file CHAY-WEB.bat.
echo Khong chay truc tiep file ben trong cua so xem ZIP.
:done
echo.
pause
