#!/usr/bin/env bash
set -e

# ==============================================================================
# AI-Фотолокация «Станок Будущего» — Скрипт запуска для Linux
# Гарантированная поддержка UTF-8 и кириллицы (Astra Linux, РЕД ОС, РОСА, Ubuntu/Debian)
# ==============================================================================

# Принудительная установка полной UTF-8 локали (ru_RU или C.UTF-8)
if locale -a 2>/dev/null | grep -qi "ru_RU.utf8"; then
    export LANG="ru_RU.UTF-8"
    export LC_ALL="ru_RU.UTF-8"
else
    export LANG="C.UTF-8"
    export LC_ALL="C.UTF-8"
fi
export PYTHONUTF8=1
export PYTHONIOENCODING="utf-8"

# Переход в директорию проекта
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "======================================================"
echo "   AI-ФОТОЛОКАЦИЯ «СТАНОК БУДУЩЕГО» (EVENT KIOSK)"
echo "======================================================"
echo ""

# Проверка и создание конфигурации .env
if [ ! -f ".env" ]; then
    echo "[INFO] Создаем базовый .env файл из .env.example..."
    cp .env.example .env
    echo "[ВНИМАНИЕ] Впишите AI_API_KEY, PRINTER_NAME и ACCESS_TOKEN в .env перед фестивалем!"
fi

# Определение интерпретатора Python (поддержка venv и .venv)
PY="python3"
if [ -f "venv/bin/python" ]; then
    PY="venv/bin/python"
elif [ -f ".venv/bin/python" ]; then
    PY=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PY="python3"
elif command -v python >/dev/null 2>&1; then
    PY="python"
fi

# Проверка виртуального окружения
if [ ! -d ".venv" ] && [ ! -d "venv" ]; then
    echo "[INFO] Создание виртуального окружения .venv..."
    $PY -m venv .venv 2>/dev/null || true
    if [ -f ".venv/bin/python" ]; then
        PY=".venv/bin/python"
    fi
fi

# Проверка кириллических шрифтов
if ls fonts/ttf/*.ttf >/dev/null 2>&1 || ls assets/fonts/*.ttf >/dev/null 2>&1; then
    echo "[INFO] Локальные TrueType-шрифты DejaVu обнаружены в проекте."
elif ! ls /usr/share/fonts/TTF/dejavu/*.ttf >/dev/null 2>&1 && ! ls /usr/share/fonts/truetype/dejavu/*.ttf >/dev/null 2>&1; then
    echo "[СОВЕТ] Для оптимальной полиграфии установите пакет шрифтов:"
    echo "  Debian/Ubuntu/MOS: sudo apt install -y fonts-dejavu-core"
    echo "  РЕД ОС / РОСА / ALT: sudo dnf install -y dejavu-sans-fonts"
fi

# Проверка и установка зависимостей
echo "[1/2] Проверка зависимостей Python (requirements.lock)..."
if [ -f "requirements.lock" ]; then
    $PY -m pip install --quiet -r requirements.lock 2>/dev/null || {
        echo "[WARN] Не удалось обновить зависимости из интернета. Запускаем с установленными пакетами."
    }
fi

# Запуск сервера
echo "[2/2] Запуск сервера и интерфейса..."
$PY run.py || {
    echo ""
    echo "[ОШИБКА] Сервер остановился с ошибкой."
    echo "  - Проверьте, не занят ли порт (обычно 8000 или 12435);"
    echo "  - Проверьте настройки в файле .env."
}

echo ""
echo "Нажмите Enter для выхода..."
read -r dummy 2>/dev/null || true
