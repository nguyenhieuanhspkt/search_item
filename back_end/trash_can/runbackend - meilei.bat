@echo off
title Khoi dong TaskApp - Port 7700 & 3000
color 0B
cls

echo ======================================================
echo [BUOC 1] DON DEP SONG HANH DOCKER & WINDOWS PORT
echo ======================================================

:: 1. Dung va xoa Container bang lenh Docker (Khoa van tong)
echo Dang dung cac Container Meilisearch...
docker stop meilisearch_vintan meilisearch_taskapp >nul 2>&1
docker rm -f meilisearch_vintan meilisearch_taskapp >nul 2>&1

:: 2. Quet va tieu diet PID tren Windows (Xa duong ong)
:: Buoc nay de diet cac tien trinh chay truc tiep .exe hoac cac phan mem khac chiem cong
for %%p in (7700,3000) do (
    for /f "tokens=5" %%a in ('netstat -aon ^| findstr :%%p') do (
        echo [CANH BAO] Phat hien PID: %%a dang chiem cong %%p. Dang giai phong...
        taskkill /F /PID %%a /T >nul 2>&1
    )
)

:: Cho 2 giay de he thong on dinh
timeout /t 2 >nul

echo.
echo [BUOC 2] KHOI CHAY MEILISEARCH (DOCKER)
echo ======================================================
:: pull never: Khong tai lai neu da co image
docker run -d --name meilisearch_taskapp ^
  -p 127.0.0.1:7700:7700 ^
  -e MEILI_MASTER_KEY=HieuVinhTan4_2026 ^
  -v "D:\TaskApp_kiet\TaskApp\meilisearch_data:/meili_data" ^
  --restart always ^
  --pull never ^
  getmeili/meilisearch:latest

echo.
echo [BUOC 3] KHOI DONG BACKEND VA FRONTEND
echo ======================================================

:: Khoi dong Backend (Uvicorn - Port 8000)
echo Dang khoi dong Backend Python...
start "Backend Server" cmd /c "cd /d D:\TaskApp_kiet\TaskApp\search_item2\search_item\back_end && D:\TaskApp_kiet\TaskApp\.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload & exit"

:: Khoi dong Frontend (React - Port 3000)
echo Dang khoi dong Frontend React...
start "Frontend React" cmd /c "cd /d D:\TaskApp_kiet\TaskApp\search_item2\search_item\front_end && npm run dev"

echo.
echo ======================================================
echo    MO TRINH DUYET TAI: http://localhost:3000
echo ======================================================
timeout /t 5
start http://localhost:3000
pause