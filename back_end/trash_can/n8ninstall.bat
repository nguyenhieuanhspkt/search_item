@echo off
title Sua loi cai dat n8n
cls

echo Dang don dep he thong...
docker system prune -a -f

echo Dang tai ban n8n on dinh (Vui long doi...)
:: Minh dung ban 1.20.0 cho nhe va on dinh
docker pull n8nio/n8n:1.20.0

echo Dang khoi chay...
docker run -d --name n8n_vinhtan -p 5678:5678 --restart always -v n8n_data:/home/node/.n8n n8nio/n8n:1.20.0

echo Xong! Hay thu vao lai localhost:5678
pause