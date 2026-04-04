@echo off
title STOP ALL SERVICES - TaskApp Unified (Full Cleanup)
color 0C

echo ======================================================
echo    DANG QUET SACH CAC TIEN TRINH TASKAPP...
echo ======================================================

:: 1. Dừng Meilisearch (Docker) an toàn
echo [1/4] Dang dung Meilisearch (Docker)...
:: Kiểm tra xem container có đang chạy không trước khi dừng
docker ps -q --filter "name=meilisearch_taskapp" >nul 2>&1
if %errorlevel% equ 0 (
    echo    - Dang gui tin hieu dung an toan den Meilisearch...
    docker stop meilisearch_taskapp >nul 2>&1
    echo    - Da dung Meilisearch thanh cong.
) else (
    echo    - Meilisearch hien khong chay hoac da dung truoc do.
)

:: 2. Diệt Python (FastAPI Backend)
echo.
echo [2/4] Dang dung Backend (Python)...
taskkill /F /IM python.exe /T /FI "STATUS eq RUNNING" >nul 2>&1
if %errorlevel% equ 0 (echo    - Da dung Python thanh cong.) else (echo    - Khong co Python dang chay.)

:: 3. Diệt Node.js / Vite (React Frontend)
echo.
echo [3/4] Dang dung Frontend (Node/Vite)...
taskkill /F /IM node.exe /T /FI "STATUS eq RUNNING" >nul 2>&1
if %errorlevel% equ 0 (echo    - Da dung Node/Vite thanh cong.) else (echo    - Khong co Node dang chay.)

:: 4. Diệt các cửa sổ CMD con đang treo
echo.
echo [4/4] Dang don dep cac cua so lenh con...
taskkill /F /FI "WINDOWTITLE eq Backend Server" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Frontend React" >nul 2>&1

echo.
echo ------------------------------------------------------
echo [OK] TAT CA DICH VU (BAO GOM MEILI) DA NGAT AN TOAN.
echo ======================================================
timeout /t 3
exit