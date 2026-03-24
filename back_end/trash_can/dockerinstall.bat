@echo off
title Cai dat Docker Desktop 4.4.4 - Vinh Tan 4
cls

echo =====================================================
echo    DANG KIEM TRA QUYEN ADMINISTRATOR...
echo =====================================================

net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Da co quyen Admin.
) else (
    echo [LOI] Vui long chuot phai vao file nay va chon 'Run as Administrator'.
    pause
    exit /b
)

echo.
echo 1. Dang don dep cac file khoa (Lock files) bi ket...
del /f /q "C:\ProgramData\chocolatey\lib\84b2b79887c621c4fdea3d797465afdb8621b29e" 2>nul
rd /s /q "C:\ProgramData\chocolatey\lib-bad" 2>nul

echo.
echo 2. Bat dau cai dat Docker Desktop phien ban 4.4.4...
echo (Qua trinh nay co the mat 5-10 phut tuy vao mang cua nha may)
echo.

choco install docker-desktop --version=4.4.4 --force -y

echo.
echo =====================================================
echo    CAI DAT HOAN TAT! 
echo    HIEU HAY KHOI DONG LAI MAY TINH (RESTART).
echo =====================================================
pause