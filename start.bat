@echo off
chcp 65001 > nul
title AI-Фотолокация "Станок Будущего"

echo ======================================================
echo    AI-ФОТОЛОКАЦИЯ «СТАНОК БУДУЩЕГО» (EVENT KIOSK)
echo ======================================================
echo.

if not exist .env (
    echo [INFO] Создаем базовый .env файл...
    copy .env.example .env > nul
)

echo [1/2] Проверка зависимостей Python...
python -m pip install --quiet -r requirements.txt

echo [2/2] Запуск сервера и интерфейса...
python run.py

pause
