@echo off
title STOP ALL SERVICES - TaskApp Unified (Precise Cleanup)
color 0C

echo ======================================================
echo     DANG NGAT CAC DICH VU TASKAPP (NHAM MUC TIEU)
echo ======================================================

:: 1. Dừng Backend trước (Dừng nguồn cấp dữ liệu)
echo [1/4] Dang dung Backend (Python)...
taskkill /F /FI "WINDOWTITLE eq Backend Server" /T >nul 2>&1
if %errorlevel% equ 0 (echo     - Da dong cua so Backend Server.) else (echo     - Khong tim thay cua so Backend.)

:: 2. Dừng Frontend (Vite/Node)
echo.
echo [2/4] Dang dung Frontend (React)...
taskkill /F /FI "WINDOWTITLE eq Frontend React" /T >nul 2>&1
if %errorlevel% equ 0 (echo     - Da dong cua so Frontend React.) else (echo     - Khong tim thay cua so Frontend.)

:: 3. Xử lý Meilisearch (Docker)
echo.
echo [3/4] Dang xu ly Meilisearch (Docker)...
docker ps -q --filter "name=meilisearch_taskapp" >nul 2>&1
if %errorlevel% equ 0 (
    echo     - Dang dung va xoa Container meilisearch_taskapp...
    docker stop meilisearch_taskapp >nul 2>&1
    docker rm -f meilisearch_taskapp >nul 2>&1
    echo     - Da giai phong cong 7700 va xoa Container.
) else (
    echo     - Meilisearch hien khong chay.
)

:: 4. Diệt các cửa sổ CMD đang giữ tiêu đề của App
echo.
echo [4/4] Dang dong cac cua so CMD...
:: Lệnh này sẽ tìm tất cả các tiến trình cmd.exe có tiêu đề tương ứng và đóng chúng
taskkill /F /FI "IMAGENAME eq cmd.exe" /FI "WINDOWTITLE eq Backend Server*" /T >nul 2>&1
taskkill /F /FI "IMAGENAME eq cmd.exe" /FI "WINDOWTITLE eq Frontend React*" /T >nul 2>&1

echo.
echo ------------------------------------------------------
echo [OK] TAT CA DICH VU DA DUOC DON DEP TRIET DE.
echo ======================================================
timeout /t 3
exit