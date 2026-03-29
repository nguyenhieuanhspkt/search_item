@echo off
title He Thong Tham Dinh - TaskApp Unified
color 0A

set BASE_PATH=D:\TaskApp_kiet\TaskApp
set BACKEND_DIR=%BASE_PATH%\search_item2\search_item\back_end
set FRONTEND_DIR=%BASE_PATH%\search_item2\search_item\front_end
set VENV_PYTHON=%BASE_PATH%\.venv\Scripts\python.exe
set MEILI_DATA_DIR=%BASE_PATH%\meilisearch_data

:: ------------------------------------------------------
echo [STEP 0] Giai phong RAM...
:: Them /FI "STATUS eq RUNNING" de tranh loi neu ko co process nao
taskkill /F /IM python.exe /T /FI "STATUS eq RUNNING" >nul 2>&1
taskkill /F /IM node.exe /T /FI "STATUS eq RUNNING" >nul 2>&1
echo [OK] Da don dep.

:: ------------------------------------------------------
echo [STEP 1] Kiem tra Docker...
:: Kiem tra xem lenh docker co ton tai ko
docker -v >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker chua duoc cai dat hoac chua add vao PATH!
    pause
    exit
)

:: Kiem tra container
docker ps -a --format "{{.Names}}" | findstr /I "meilisearch_taskapp" >nul
if %errorlevel% == 0 (
    echo [DOCKER] Dang start Meilisearch...
    docker start meilisearch_taskapp
) else (
    echo [DOCKER] Dang create Meilisearch...
    docker run -d --name meilisearch_taskapp -p 7700:7700 -e MEILI_MASTER_KEY=HieuVinhTan4_2026 -v "%MEILI_DATA_DIR%:/meili_data" --restart always getmeili/meilisearch:latest
)

:: ------------------------------------------------------
echo [STEP 2] Khoi dong Backend...
if not exist "%VENV_PYTHON%" (
    echo [ERROR] Khong tim thay file %VENV_PYTHON%
    pause
    exit
)
start "Backend Server" cmd /k "cd /d %BACKEND_DIR% && %VENV_PYTHON% -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

:: ------------------------------------------------------
echo [STEP 3] Khoi dong Frontend...
start "Frontend React" cmd /k "cd /d %FRONTEND_DIR% && npm run dev"

echo ======================================================
echo    MOI THU DA OK! DANG MO TRINH DUYET...
echo ======================================================
timeout /t 5
start http://localhost:3000
pause