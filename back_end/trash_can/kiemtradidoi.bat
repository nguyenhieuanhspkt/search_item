@echo off
title Kiem tra vi tri du lieu Docker - Vinh Tan 4
cls
color 0B

echo =====================================================
echo    HE THONG KIEM TRA DI DOI DOCKER
echo =====================================================
echo.

echo 1. Dang kiem tra trang thai cac goi WSL...
wsl -l -v
echo.

echo 2. Dang soi "Nha Cu" tai o C...
if exist "%LOCALAPPDATA%\Docker\wsl\data\ext4.vhdx" (
    echo [!] CANH BAO: Van thay file du lieu nang tai o C!
    dir "%LOCALAPPDATA%\Docker\wsl\data\ext4.vhdx" | findstr "vhdx"
) else (
    echo [OK] O C da sach bong kin kit!
)
echo.

echo 3. Dang soi "Nha Moi" tai o D...
if exist "D:\Docker_Data\data\ext4.vhdx" (
    echo [OK] DA THAY file du lieu tai o D:
    dir "D:\Docker_Data\data\ext4.vhdx" | findstr "vhdx"
) else (
    echo [!] LOI: Khong tim thay du lieu tai D:\Docker_Data\data\
)

echo.
echo =====================================================
echo    KET LUAN:
echo =====================================================
if exist "D:\Docker_Data\data\ext4.vhdx" (
    if not exist "%LOCALAPPDATA%\Docker\wsl\data\ext4.vhdx" (
        color 0A
        echo === CHUC MUNG! HIEU DA DI DOI THANH CONG 100%% ===
    ) else (
        color 0E
        echo === CAN TRONG: Du lieu dang nam o ca 2 noi. Hay xoa o C di ===
    )
) else (
    color 0C
    echo === THAT BAI: Du lieu van dang nam o o C ===
)
echo =====================================================
pause