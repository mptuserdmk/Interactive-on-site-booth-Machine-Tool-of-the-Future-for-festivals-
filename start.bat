@echo off
chcp 65001 > nul
title AI-Фотолокация "Станок Будущего"
cd /d "%~dp0"

echo ======================================================
echo    AI-ФОТОЛОКАЦИЯ «СТАНОК БУДУЩЕГО» (EVENT KIOSK)
echo ======================================================
echo.

if not exist .env (
    echo [INFO] Создаем базовый .env файл из .env.example...
    copy .env.example .env > nul
    echo [ВНИМАНИЕ] Впишите AI_API_KEY, PRINTER_NAME и ACCESS_TOKEN в .env перед фестивалем!
)

echo [1/2] Проверка зависимостей Python (закреплённые версии из requirements.lock)...
python -m pip install --quiet -r requirements.lock
if errorlevel 1 (
    echo [WARN] Не удалось установить зависимости ^(нет интернета?^). Пробуем запустить с уже установленными.
)

echo [2/2] Запуск сервера и интерфейса...
python run.py
if errorlevel 1 (
    echo.
    echo [ОШИБКА] Сервер остановился с ошибкой. Частые причины:
    echo   - порт 8000 занят другой программой ^(закройте её или задайте PORT в .env^);
    echo   - ошибка в .env ^(строка с именем параметра выше в сообщении^).
)

pause
