@echo off
title He thong Don dep O C - Vinh Tan 4
chcp 65001 > nul

:: 1. Kiểm tra quyền Administrator (Bắt buộc để chạy powercfg)
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] BẠN CẦN CHẠY FILE NÀY VỚI QUYỀN ADMINISTRATOR.
    echo [!] Chuột phải vào file và chọn "Run as Administrator".
    pause
    exit /b
)

echo ---------------------------------------------------
echo ĐANG KÍCH HOẠT MÔI TRƯỜNG ẢO VÀ CHẠY SCRIPT...
echo ---------------------------------------------------

:: 2. Đường dẫn đến Python trong venv của bạn
set VENV_PYTHON="D:\TaskApp_kiet\TaskApp\.venv\Scripts\python.exe"
:: 3. Đường dẫn đến file script của bạn
set SCRIPT_PATH="D:\TaskApp_kiet\TaskApp\cleanCdrive\cleanCdrive.py"

:: 4. Thực thi
if exist %VENV_PYTHON% (
    %VENV_PYTHON% %SCRIPT_PATH%
) else (
    echo [!] Khong tim thay moi truong ao tai: %VENV_PYTHON%
    echo [!] Dang thu chay bang Python he thong...
    python %SCRIPT_PATH%
)

echo.
echo ---------------------------------------------------
echo HOÀN TẤT QUÁ TRÌNH!
echo ---------------------------------------------------
pause