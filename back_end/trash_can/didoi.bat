@echo off
title Di doi du lieu Docker sang o D - Vinh Tan 4
cls

echo =====================================================
echo    BUOC 1: KIEM TRA QUYEN ADMIN...
echo =====================================================
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [LOI] Vui long chuot phai vao file nay chon 'Run as Administrator'.
    pause
    exit /b
)

echo [OK] Da co quyen Admin.
echo.
echo =====================================================
echo    BUOC 2: YEU CAU TAT DOCKER DESKTOP
echo =====================================================
echo Hieu hay CHUOT PHAI vao bieu tuong con ca voi o goc man hinh,
echo chon 'Quit Docker Desktop' truoc khi tiep tuc!
echo.
pause

echo.
echo 3. Dang tao thu muc luu tru moi tren o D...
if not exist "D:\Docker_Data" mkdir "D:\Docker_Data"

echo.
echo 4. Dang xuat du lieu (Export) sang o D...
echo (Buoc nay co the mat vai phut, Hieu vui long cho...)
wsl --export docker-desktop-data D:\Docker_Data\docker-desktop-data.tar

if %errorLevel% neq 0 (
    echo [LOI] Khong tim thay goi du lieu Docker. Hay chac chan Docker da duoc cai dat.
    pause
    exit /b
)

echo.
echo 5. Dang xoa goi du lieu cu tai o C (Unregister)...
wsl --unregister docker-desktop-data

echo.
echo 6. Dang nap du lieu (Import) vao vi tri moi o D...
wsl --import docker-desktop-data D:\Docker_Data\data D:\Docker_Data\docker-desktop-data.tar --version 2

echo.
echo 7. Dang don dep file tam...
del /f /q D:\Docker_Data\docker-desktop-data.tar

echo.
echo =====================================================
echo    DI DOI THANH CONG!
echo    Bay gio Hieu co the mo lai Docker Desktop.
echo    O C cua Hieu se "tho" hon rat nhieu roi day!
echo =====================================================
pause