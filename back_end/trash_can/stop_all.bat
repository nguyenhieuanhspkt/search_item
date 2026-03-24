@echo off
title STOP ALL SERVICES - TaskApp Unified
color 0C

echo ======================================================
echo    DANG QUET SACH CAC TIEN TRINH TASKAPP...
echo ======================================================

:: 1. Diệt Python (FastAPI Backend)
echo [1/3] Dang dung Backend (Python)...
taskkill /F /IM python.exe /T >nul 2>&1
if %errorlevel% equ 0 (echo    - Da dung Python thanh cong.) else (echo    - Khong co Python dang chay.)

:: 2. Diệt Node.js / Vite (React Frontend)
echo [2/3] Dang dung Frontend (Node/Vite)...
taskkill /F /IM node.exe /T >nul 2>&1
if %errorlevel% equ 0 (echo    - Da dung Node/Vite thanh cong.) else (echo    - Khong co Node dang chay.)

:: 3. Diệt các cửa sổ CMD con đang treo (Nếu có)
echo [3/3] Dang don dep cac cua so lenh con...
taskkill /F /FI "WINDOWTITLE eq Backend Server" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Frontend React" >nul 2>&1

echo ------------------------------------------------------
echo [OK] TAT CA DICH VU DA DUOC NGAT KET NOI AN TOAN.
echo ======================================================
timeout /t 3
exit