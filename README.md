# Astralio — Telegram-бот MVP (Астрология и Таро)

Полноценный рабочий MVP Telegram-бота **Astralio** на Python 3.12+ с реальными эфемеридными расчётами (**Swiss Ephemeris / `pyswisseph`**), хранением данных в **Google Cloud Firestore**, чистой модульной архитектурой, тестами (`pytest` + `pytest-asyncio`) и CI (Ruff + pytest).

---

## Возможности MVP

1. **Регистрация и профиль**
   - Автоматическая регистрация при `/start` или первом обращении (Telegram ID, имя, фамилия, username).
   - Сохранение и редактирование даты, времени и места рождения в Firestore (`users/{telegram_id}`).
   - Встроенный справочник городов (Россия, СНГ, мир), парсер прямых координат (`широта, долгота`), определение часового пояса (`timezonefinder`) и опциональный геокодер OpenStreetMap Nominatim.
2. **Натальная карта**
   - Пошаговый сбор данных рождения с валидацией, кнопками «Назад» и «Отмена».
   - Реальный расчёт положений Солнца, Луны, Меркурия, Венеры, Марса, Юпитера, Сатурна, Урана, Нептуна и Плутона через `pyswisseph` (встроенные эфемериды Moshier).
   - Расчёт Асцендента (ASC), Середины Неба (MC), 12 домов (система Плацидуса; для широт выше 66° — полнознаковая система) и мажорных аспектов.
   - Если точное время рождения или координаты неизвестны — расчёт выполняется на 12:00 UTC без выдумывания домов/Асцендента, с явным выводом ограничений.
3. **Совместимость (синастрия)**
   - Сравнение своего профиля с партнёром или ввод данных двух людей шаг за шагом.
   - Реальные межкартовые (синастрические) аспекты и баланс стихий.
   - Понятные оценки по сферам (эмоции, романтика, общение, долгосрочный потенциал), сильные стороны, зоны внимания и практическая рекомендация.
4. **Персональные прогнозы**
   - Ежедневный (1 день) и недельный (7 дней) прогноз.
   - Расчёт реальных текущих транзитов планет к натальной карте пользователя через Swiss Ephemeris.
   - Без заполненной даты рождения бот честно предлагает заполнить профиль вместо подмены случайным текстом.
5. **Таро**
   - Полная колода из 78 карт (22 Старших и 56 Младших Арканов) на русском языке.
   - 4 расклада: *Карта дня* (1), *Прошлое · Настоящее · Будущее* (3), *Отношения* (3), *Выбор пути* (5).
   - Криптографически честная выборка без повторов внутри расклада (`secrets.SystemRandom().sample`), прямое и перевёрнутое положение карт.
   - Автоматическое сохранение и просмотр истории раскладов в Firestore (`users/{telegram_id}/tarot_readings`).
6. **Premium и Telegram Stars**
   - Страница тарифов (1 месяц, 3 месяца, 1 год) и проверка реального статуса подписки.
   - Подготовленная архитектура оплаты через **Telegram Stars (`XTR`)**: `send_invoice`, `PreCheckoutQueryHandler`, `SUCCESSFUL_PAYMENT` и идемпотентный реестр платежей (`payments/{charge_id}`) с защитой от повторной обработки.
   - При `TELEGRAM_STARS_ENABLED=false` оплата не имитируется и подписка никогда не активируется без реального подтверждённого платежа Telegram.
7. **Помощь и обратная связь**
   - Подробная инструкция по всем функциям.
   - Пошаговая форма обратной связи с сохранением в Firestore (`feedback/{feedback_id}`).
   - Корректная обработка неизвестных команд, некорректного ввода и поддельных/устаревших `callback_data`.

---

## Архитектура проекта

```text
astralio/
├── main.py                  # Точка входа (polling для Railway Worker, безопасное завершение)
├── app.py                   # Сборка зависимостей и python-telegram-bot Application
├── config.py                # Pydantic Settings (валидация env-переменных, SecretStr)
├── models/                  # Pydantic-модели (user, astrology, tarot, payment, feedback)
├── infrastructure/          # Firebase/Firestore init, геокодинг, логирование с маскировкой секретов
├── repositories/            # Асинхронные репозитории Firestore (user, reading, payment, feedback)
├── services/                # Бизнес-логика (astrology, compatibility, forecast, tarot, ai, premium, user, validators)
├── keyboards/               # InlineKeyboardMarkup и строгий реестр callback_data
└── handlers/                # Обработчики команд, ConversationHandler-ы и защита от ошибок
tests/                       # Автотесты pytest + pytest-asyncio (с моками, без реальных секретов)
.github/workflows/ci.yml     # GitHub Actions CI: Ruff + pytest
```

---

## Переменные окружения

Скопируйте `.env.example` в `.env` и заполните значения:

```bash
cp .env.example .env
```

### Обязательные переменные

| Переменная | Описание |
| --- | --- |
| `BOT_TOKEN` | Токен Telegram-бота от `@BotFather` |
| `FIREBASE_PROJECT_ID` | ID проекта Firebase / Google Cloud |
| `FIREBASE_CLIENT_EMAIL` | `client_email` из JSON-ключа сервисного аккаунта Firebase |
| `FIREBASE_PRIVATE_KEY` | `private_key` из JSON-ключа (можно в одну строку с `\n`) |

### Необязательные переменные

| Переменная | По умолчанию | Описание |
| --- | --- | --- |
| `FIREBASE_DATABASE_ID` | *(пусто — `(default)`)* | Имя именованной базы Firestore |
| `AI_API_KEY` | *(пусто)* | Ключ OpenAI-совместимого API для расширения интерпретаций. Если пусто — работает полноценный локальный расчёт без ИИ |
| `AI_BASE_URL` | `https://api.openai.com/v1` | Базовый URL API языковой модели |
| `AI_MODEL` | `gpt-4o-mini` | Название модели |
| `AI_TIMEOUT_SECONDS` | `15` | Таймаут запроса к AI-сервису (сек.) |
| `AI_RATE_LIMIT_PER_MINUTE` | `5` | Лимит AI-запросов на пользователя в минуту |
| `TELEGRAM_STARS_ENABLED` | `false` | Включить выставление счетов Telegram Stars (`XTR`) после настройки в `@BotFather` |
| `GEOCODING_ENABLED` | `true` | Разрешить удалённый поиск редких городов через Nominatim (офлайн-справочник работает всегда) |
| `LOG_LEVEL` | `INFO` | Уровень логирования (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

---

## Подготовка Firebase и Telegram

1. **Telegram Bot**:
   - Откройте `@BotFather`, выполните `/newbot` и получите `BOT_TOKEN`.
2. **Firebase Firestore**:
   - Создайте проект в [Firebase Console](https://console.firebase.google.com/) и включите **Cloud Firestore**.
   - Перейдите в *Project Settings → Service Accounts → Generate new private key*.
   - Скопируйте из скачанного JSON значения `project_id`, `client_email`, `private_key` в переменные окружения. **Не добавляйте JSON-файл в Git!**

---

## Локальный запуск

Требуется **Python 3.12+**.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Создайте `.env` на основе `.env.example`, затем запустите бота:

```bash
python -m astralio.main
```

---

## Проверка качества (Ruff и pytest)

Тесты полностью автономны, используют моки Firestore/Telegram и **не требуют реальных секретов**:

```bash
ruff check astralio tests
ruff format --check astralio tests
pytest -v
```

---

## Развёртывание на Railway (Worker / Polling)

1. Подключите GitHub-репозиторий в [Railway](https://railway.app/).
2. Убедитесь, что сервис запускается как **Worker** со стартовой командой из `Procfile`:
   ```text
   python -m astralio.main
   ```
3. Добавьте переменные окружения в разделе **Variables** проекта Railway (`BOT_TOKEN`, `FIREBASE_PROJECT_ID`, `FIREBASE_CLIENT_EMAIL`, `FIREBASE_PRIVATE_KEY`, при необходимости `FIREBASE_DATABASE_ID`, `AI_API_KEY`, `TELEGRAM_STARS_ENABLED`).
4. Railway автоматически соберёт зависимости из `requirements.txt` и запустит polling-воркер.
