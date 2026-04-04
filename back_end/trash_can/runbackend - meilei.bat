@echo off
title Khoi dong TaskApp - Port 7700
color 0B
cls

echo ======================================================
echo [BUOC 1] QUET SACH CONG 7700...
echo ======================================================

:: Tim tat ca cac PID dang dung cong 7700 va tieu diet tan goc
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :7700') do (
    echo [CANH BAO] Phat hien ke chiem dong PID: %%a. Dang tieu diet...
    taskkill /F /PID %%a /T >nul 2>&1
)

:: Cho 1 giay de Windows cap nhat lai bang mang
timeout /t 1 >nul

echo.
echo [BUOC 2] DON DEP DOCKER CU...
docker rm -f meilisearch_taskapp >nul 2>&1

echo.
echo [BUOC 3] KHOI CHAY LAI MEILISEARCH (PORT 7700)
echo ======================================================
:: Ep Docker bind vao IPv4 127.0.0.1 de tranh xung dot IPv6 cua Windows
docker run -d --name meilisearch_taskapp ^
  -p 127.0.0.1:7700:7700 ^
  -e MEILI_MASTER_KEY=HieuVinhTan4_2026 ^
  -v "D:\TaskApp_kiet\TaskApp\meilisearch_data:/meili_data" ^
  --restart always getmeili/meilisearch:latest

echo.
echo [BUOC 4] KHOI DONG BACKEND & FRONTEND...
:: (Phan nay Hiếu giu nguyen nhu file cu cua ban)
start "Backend Server" cmd /k "cd /d D:\TaskApp_kiet\TaskApp\search_item2\search_item\back_end && D:\TaskApp_kiet\TaskApp\.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
start "Frontend React" cmd /k "cd /d D:\TaskApp_kiet\TaskApp\search_item2\search_item\front_end && npm run dev"

echo.
echo ======================================================
echo    DA LAY LAI CONG 7700 THANH CONG!
echo ======================================================
timeout /t 5
start http://localhost:3000
pause