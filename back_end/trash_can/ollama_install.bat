@echo off
title Thiet lap Ollama API vơi Docker
cls

echo [BUOC 1] Dang kiem tra trang thai Docker...
docker ps >nul 2>&1
if %errorLevel% neq 0 (
    echo [LOI] Docker chua chay. Vui long mo Docker Desktop truoc.
    pause
    exit /b
)

echo [BUOC 2] Dang khoi tao Container Ollama...
:: Su dung port 11434 truyen thong cua Ollama
docker run -d ^
  --name ollama ^
  -p 11434:11434 ^
  -v ollama_data:/root/.ollama ^
  --restart always ^
  ollama/ollama

echo [BUOC 3] Dang doi API san sang (5s)...
timeout /t 5 /nobreak >nul

echo [BUOC 4] Tai model Embedding BGE-M3...
:: Lenh nay goi API noi bo de tai model
docker exec -it ollama ollama pull bge-m3

echo.
echo ==========================================
echo    THIET LAP HOAN TAT!
echo ==========================================
echo API URL cho n8n: http://host.docker.internal:11434
echo Model Embedding: bge-m3
echo ==========================================
pause