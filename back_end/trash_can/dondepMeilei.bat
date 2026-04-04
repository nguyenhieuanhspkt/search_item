@echo off
title TRUY QUET CONG 7700
color 0C
cls

echo Dang tim ke dang chiem giu cong 7700...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :7700') do (
    echo [PHAT HIEN] PID: %%a dang chiem port. Dang cuong che xoa...
    taskkill /F /PID %%a /T
)

echo.
echo Dang xoa container cu...
docker rm -f meilisearch_taskapp >nul 2>&1

echo.
echo Dang thu khoi dong lai voi PORT KHAC (7701) de kiem tra...
echo (Neu 7700 bi kien co qua, ta dung 7701 cho nhanh viec)
docker run -d --name meilisearch_taskapp -p 127.0.0.1:7701:7700 getmeili/meilisearch:latest

echo.
echo ======================================================
docker ps --filter "name=meilisearch_taskapp"
echo ======================================================
echo LUU Y: Neu thay STATUS la "Up", hay dung port 7701 trong code nhe!
pause