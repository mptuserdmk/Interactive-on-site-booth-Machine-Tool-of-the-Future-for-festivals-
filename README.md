# ⚡ AI-Фотолокация «Станок Будущего» (Interactive Event Kiosk)

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg?style=flat-square&logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![OpenCV](https://img.shields.io/badge/OpenCV-Camera_HUD-5C3EE8.svg?style=flat-square&logo=opencv)](https://opencv.org/)
[![Pillow](https://img.shields.io/badge/Pillow-300_DPI_Composer-FFB000.svg?style=flat-square)](https://python-pillow.org/)
[![Architecture](https://img.shields.io/badge/Architecture-Local--First-brightgreen.svg?style=flat-square)]()
[![Status](https://img.shields.io/badge/Status-Production_Ready-success.svg?style=flat-square)]()

Интерактивный программно-аппаратный комплекс для фестивалей, форумов и выставок: генерация персонализированного паспорта инженера будущего, 100 уникальных комбинаций профессий, поддержка тачскринов/планшетов, съемка по USB и по воздуху (OTA) через iPhone/Android, Pillow-композиция 300 DPI и прямая печать на фотопринтере.

---

## 🌟 Ключевые возможности

### 1. 🖥️ Touchscreen / Tablet Kiosk UI
- **Интерфейс под большие сенсорные панели и планшеты:** крупные элементы управления, комфортные для пальца тап-зоны, высокая контрастность и темная индустриальная эстетика (Linear / Swiss Engineering Style).
- **Плавный отклик (0.5s Tactile Feedback):** тактильная анимация выбора карточек с выверенной паузой для фиксации решения участника.
- **Автосброс при бездействии (KFC-Style Idle Timeout):** при отсутствии активности в течение 15 секунд открывается окно с 5-секундным таймером обратного отсчета для возврата на стартовый экран.

### 2. 📸 Двойной контур съемки (USB + По воздуху)
- **USB / Встроенная камера:** прямое подключение через OpenCV с неблокирующим потоком, прицельной сеткой калибровки и зеркалированием.
- **По воздуху (iPhone / Android OTA):** ассистент сканирует QR-код на панели оператора, открывает мобильную веб-камеру (`/mobile-camera`) и делает снимок прямо со смартфона. Фото моментально отправляется на экран киоска по локальному Wi-Fi.

### 3. 🧬 100 Комбинаций профессий (Quiz Engine)
- **Стихии (5):** Космос, Атом, Роботы, Медицина, Металл.
- **Суперсилы (5):** Точность, Скорость, Сила, Ум, Забота.
- **Цвета (4):** Лазурный (`#00D2FF`), Золотой (`#FFD700`), Изумрудный (`#00FF88`), Белый (`#FFFFFF`).
- **100 готовых карточек** с реальными научно-производственными центрами (*Роскосмос, Росатом, Курчатовский институт, НПО Энергомаш, ЦНИИ РТК, Северсталь* и др.).

### 4. 🖨️ Графический Pillow Composer и Печать
- Генерация паспорта-пропуска в печатном качестве 300 DPI (10×15 см).
- Наложение неоновой рамки, AI-портрета, суперсилы, завода и персонализированного QR-кода на скачивание.
- **Быстрая повторная печать (Reprint):** моментальная допечатка карточки из истории оператора без повторного вызова AI.

### 5. 🤖 Модульный AI Abstraction Layer
- `MockProvider` (по умолчанию) — автономная офлайн-работа без затрат на API для тестов и выставок со слабым интернетом.
- Поддержка облачных генераторов `Fal.ai` (Flux / SDXL) и `Replicate` (FaceID / Photomaker).
- Автоматический Fallback: стенд не падает при сбоях сети.

---

## 🚀 Быстрый запуск

### Способ 1: Запуск в 1 клик на Windows
Дважды нажмите на файл:
```cmd
start.bat
```

### Способ 2: Запуск через консоль
```bash
# 1. Установка зависимостей
pip install -r requirements.txt

# 2. Запуск приложения
python run.py
```

---

## 🌐 Ссылки системы после запуска

| Назначение | Адрес | Описание |
| :--- | :--- | :--- |
| 🖥️ **Киоск посетителя** | `http://localhost:8000/kiosk` | Сенсорный интерфейс для участников фестиваля |
| 🎛️ **Панель оператора** | `http://localhost:8000/operator` | Мониторинг оборудования, история и кнопка `REPRINT` |
| 📱 **Камера iPhone (OTA)** | `http://<IP-ПК>:8000/mobile-camera` | Беспроводная съемка со смартфона по Wi-Fi |
| 📚 **OpenAPI Swagger** | `http://localhost:8000/docs` | Интерактивная документация REST API |

---

## ⚙️ Конфигурация (`.env`)

Создайте файл `.env` (на базе `.env.example`):

```env
# AI Провайдер: mock (офлайн/бесплатно), fal (Fal.ai Flux/SDXL), replicate (Replicate FaceID)
AI_PROVIDER=mock
AI_API_KEY=

# Настройки камеры
CAMERA_INDEX=0
CAMERA_WIDTH=1920
CAMERA_HEIGHT=1080
CAMERA_FPS=30
CAMERA_MIRROR=true

# Настройки принтера
PRINTER_NAME=
ENABLE_AUTO_PRINT=true
PRINT_SIMULATION_MODE=false

# Политика приватности
DELETE_SOURCE_PHOTOS_AFTER_PRINT=true

# Брендинг
FESTIVAL_NAME=FUTURE INDUSTRY 2026
FESTIVAL_HASHTAG=#ФЕСТИВАЛЬ2026
```

---

## 📂 Структура репозитория

```text
ai-festival-kiosk/
├── app/
│   ├── main.py                  # Точка входа FastAPI, статика, шаблоны, OpenAPI
│   ├── config/settings.py       # Автоопределение локального IP для iPhone
│   ├── api/                     # REST API и WebSocket роуты
│   ├── camera/manager.py        # USB захват (OpenCV) и Mobile OTA Upload
│   ├── quiz/combinations.py     # Индекс 100 комбинаций
│   ├── ai/                      # AI провайдеры (Mock, Fal.ai, Replicate) + Fallback
│   ├── composition/composer.py  # Pillow сборка печатного бейджа 300 DPI
│   ├── printing/manager.py      # Управление печатью Windows Spooler и Reprint
│   └── storage/database.py      # SQLite база сессий
├── data/combinations.json       # Полный датасет 100 профессий
├── frontend/
│   ├── templates/               # Kiosk, Operator, Mobile Camera, Digital Card
│   └── static/                  # Стили Touchscreen UI и логика Kiosk JS
├── tests/                       # Интеграционные тесты полного жизненного цикла
├── start.bat                    # Windows 1-click launcher
├── requirements.txt             # Зависимости Python
└── README.md                    # Документация проекта
```

---

## 🧪 Запуск тестов

Для проверки работоспособности всех эндпоинтов, камеры, генератора и базы:
```bash
python tests/test_full_lifecycle.py
```
