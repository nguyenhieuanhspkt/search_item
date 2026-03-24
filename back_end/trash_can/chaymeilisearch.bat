@echo off
title Kich hoat Meilisearch - Vinh Tan 4
cls
color 0A

echo =====================================================
echo    HE THONG KICH HOAT KHO DU LIEU MEILISEARCH
echo =====================================================
echo.

:: 1. Kiem tra Docker co dang chay khong
docker info >nul 2>&1
if %errorLevel% neq 0 (
    color 0C
    echo [LOI] Docker chua duoc bat! 
    echo Hieu hay mo Docker Desktop va doi con ca voi dung yen nhe.
    pause
    exit /b
)

echo [OK] Docker dang san sang.
echo.

:: 2. Kiem tra xem container da ton tai chua
docker ps -a --format "{{.Names}}" | findstr /X "meilisearch_vintan" >nul
if %errorLevel% == 0 (
    echo [OK] Da tim thay container 'meilisearch_vintan'.
    echo Dang bat dau kich hoat...
    docker start meilisearch_vintan
) else (
    echo [!] Khong tim thay container. Dang tien hanh tao moi...
    echo Dang thiet lap du lieu tai D:\Meilisearch_Data...
    
    if not exist "D:\Meilisearch_Data" mkdir "D:\Meilisearch_Data"

    docker run -d ^
      -p 7700:7700 ^
      -v D:\Meilisearch_Data:/meili_data ^
      --name meilisearch_vintan ^
      --restart always ^
      getmeili/meilisearch:v1.5 ^
      meilisearch --master-key "HieuVinhTan4_2026"
)

echo.
echo =====================================================
echo    DA KICH HOAT THANH CONG!
echo    Hieu co the vao: http://localhost:7700
echo    Master Key: HieuVinhTan4_2026
echo =====================================================
echo.
echo Dang mo trinh duyet kiem tra...
start http://localhost:7700
pause