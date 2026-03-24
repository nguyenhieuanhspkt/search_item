@echo off
title He Thong Tham Dinh - TaskApp Unified (Auto-Clean & Lazy-Load)
color 0A

:: ======================================================
:: BUOC 0: DON DEP HE THONG (RAT QUAN TRONG CHO MAY KHONG GPU)
:: ======================================================
echo [CLEAN] Dang quet sach cac tien trinh chay ngam de giai phong RAM...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM node.exe /T >nul 2>&1
echo [OK] Da don dep xong. RAM da san sang!
echo ------------------------------------------------------

:: 1. THIET LAP DUONG DAN
:: Hiếu kiểm tra lại BASE_PATH có đúng thư mục chứa .venv không nhé
set BASE_PATH=D:\TaskApp_kiet\TaskApp
set BACKEND_DIR=%BASE_PATH%\search_item2\search_item\back_end
set FRONTEND_DIR=%BASE_PATH%\search_item2\search_item\front_end
set VENV_PYTHON=%BASE_PATH%\.venv\Scripts\python.exe

:: 2. KHOI DONG BACKEND
echo [STEP 1/3] Dang khoi dong Backend (Port 8000)...
:: Luu y: Minh vao thang thu muc back_end de chay main.py
start "Backend Server" cmd /k "cd /d %BACKEND_DIR% && %VENV_PYTHON% -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 3 >nul

:: 3. KHOI DONG FRONTEND
echo [STEP 2/3] Dang khoi dong Frontend (Port 3000)...
start "Frontend React" cmd /k "cd /d %FRONTEND_DIR% && npm run dev"

:: 4. DOI VA MO UNG DUNG
echo [STEP 3/3] Dang doi he thong on dinh...
for /l %%i in (8,-1,1) do (
    cls
    echo ======================================================
    echo    DANG KHOI DONG HE THONG... CON %%i GIAY
    echo    (Luu y: Chế độ AI sẽ nạp khi bạn nhấn Tìm kiếm lần đầu)
    echo ======================================================
    timeout /t 1 >nul
)

:: MO TRINH DUYET O CONG 3000 (Vite)
start http://localhost:3000

echo ======================================================
echo    DA SAN SANG! HIU NGUYEN CO THE LAM VIEC.
echo    Backend: http://localhost:8000
echo    Frontend: http://localhost:3000
echo ======================================================
pause