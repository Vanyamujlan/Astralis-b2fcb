# ПОЛНЫЙ ТЕХНИЧЕСКИЙ АУДИТ ASTRALIO

**Дата аудита:** `2026-11-21`  
**Версия проекта:** `0.1.0` (`pyproject.toml:3`)  
**Проверенный бот:** `@Astraliio_bot` (Telegram Bot ID `9087181425`)  
**Статус кода во время аудита:** только чтение и диагностика (рабочий код бота, Firebase и секреты не изменялись).

---

## 1. Архитектура системы

Astralio реализован как модульное асинхронное приложение на **Python 3.12+** (`pyproject.toml:6`, фактическая среда `.venv`: `Python 3.12.16`) с чётким разделением на слои (Clean / Layered Architecture):

1. **Точка входа и жизненный цикл:**
   - `astralio/main.py` (`main()`) — загрузка `Settings`, настройка безопасного логирования (`configure_logging`), сборка приложения (`build_application`), запуск long-polling (`application.run_polling(allowed_updates=ALLOWED_UPDATES)`).
   - `astralio/app.py` (`build_service_container()`, `build_application()`, `_post_init()`) — Dependency Injection через `ServiceContainer`, сохраняемый в `app.bot_data[SERVICES_BOT_DATA_KEY]`.
   - Для локального запуска внутри Google AI Studio используется обёртка `server.ts` (`startPythonBot()`), которая запускает `.venv/bin/python -m astralio.main` дочерним процессом с наследованием секретов `process.env`, экранированием секретов в логах (`redactSecrets()`) и безопасным диагностическим эндпоинтом `GET /api/bot-status`.
2. **Слой презентации и маршрутизации (`handlers/` + `keyboards/`):**
   - `python-telegram-bot 22.8` (`Application`, `ConversationHandler`, `CallbackQueryHandler`, `CommandHandler`, `PreCheckoutQueryHandler`, `MessageHandler`).
   - Жёсткий порядок регистрации в `astralio/handlers/__init__.py:25-60`: сначала 5 `ConversationHandler`, затем глобальные команды и меню 7 модулей, затем платёжные обработчики Stars, и последними — fallback-перехватчики и `global_error_handler`.
3. **Слой бизнес-логики (`services/`):** чистые Python-сервисы без прямой привязки к объектам `telegram.Update` (`AstrologyService`, `CompatibilityService`, `ForecastService`, `TarotService`, `PremiumService`, `UserService`, `AIService`, `validators`).
4. **Слой доступа к данным (`repositories/`):** `UserRepository`, `ReadingRepository`, `PaymentRepository`, `FeedbackRepository` — изолируют синхронные вызовы Firestore SDK в `asyncio.to_thread(...)`, не блокируя event loop.
5. **Инфраструктурный слой (`infrastructure/`):** `firebase.py`, `local_store.py`, `geocoding.py`, `logging.py`.
6. **Модели данных (`models/`):** типизированные модели (`user.py`, `astrology.py`, `tarot.py`, `payment.py`, `feedback.py`).

---

## 2. Структура проекта

Фактическая проверка командой `find astralio tests -maxdepth 3 -type f ! -path '*__pycache__*' | sort` подтвердила **41 файл в `astralio/`** и **10 файлов в `tests/`**:

```text
astralio/
├── __init__.py, app.py, config.py, main.py
├── handlers/       (__init__.py, common.py, compatibility.py, deps.py, forecast.py,
│                    help.py, natal.py, premium.py, profile.py, tarot.py)
├── infrastructure/ (__init__.py, firebase.py, geocoding.py, local_store.py, logging.py)
├── keyboards/      (__init__.py, callbacks.py, menus.py)
├── models/         (__init__.py, astrology.py, feedback.py, payment.py, tarot.py, user.py)
├── repositories/   (__init__.py, base.py, feedback_repository.py, payment_repository.py,
│                    reading_repository.py, user_repository.py)
└── services/       (__init__.py, ai_service.py, astrology_service.py, compatibility_service.py,
                     forecast_service.py, premium_service.py, tarot_deck.py, tarot_service.py,
                     user_service.py, validators.py)

tests/
├── conftest.py
├── test_ai_service.py
├── test_astrology_service.py
├── test_callbacks_and_config.py
├── test_compatibility_service.py
├── test_forecast_service.py
├── test_handlers.py
├── test_premium_service.py
├── test_repositories.py
└── test_tarot_service.py
```

Дополнительные файлы развёртывания и веб-оболочки:
- `Procfile` (`worker: python -m astralio.main`), `.github/workflows/ci.yml`, `pyproject.toml`, `requirements.txt`, `server.ts`, `firestore.rules`, `firebase-applet-config.json`, `src/firebase.ts`, `src/App.tsx`.

---

## 3. Работа Telegram Bot API (живая проверка)

Фактический запрос `GET http://127.0.0.1:3000/api/bot-status` на `2026-11-21`:
- **Статус процесса:** `"running": true`, `pid: 1352`, `exitCode: null`, `lastError: null`.
- **Токен:** `"hasBotToken": true`, `"tokenSourceKey": "BOT_TOKEN"`.
- **Подтверждённая авторизация в Telegram API (`_post_init` в `astralio/app.py:83-93`):**
  `Telegram Bot API connected successfully: @Astraliio_bot (id=9087181425)` и `telegram.ext.Application | Application started`.
- **Живое взаимодействие:** логи содержат 6 реальных обращений пользователя к боту в `11:53–11:59 UTC` и создан файл локальной БД `.astralio_local_db.json` (2 638 байт, обновлён `Nov 21 11:59`).
- **Регистрируемое меню команд (`astralio/app.py:87-93`):** `/start`, `/menu`, `/cancel`.
- **Разрешённые типы апдейтов (`astralio/app.py:116-120`):** `Update.MESSAGE`, `Update.CALLBACK_QUERY`, `Update.PRE_CHECKOUT_QUERY`.

---

## 4. Все команды и кнопки (покрытие 100%)

- **Slash-команды (`astralio/handlers/common.py:165-179`):**
  - `/start` → `start_command` (очистка `user_data`, авто-регистрация через `ensure_user`, показ главного меню).
  - `/menu` → `menu_command` (возврат в главное меню).
  - `/cancel` → `cancel_operation` (отмена любого активного шага диалога).
  - Неизвестные команды (`filters.COMMAND`) → `unknown_command_handler` (вежливый ответ со списком команд и главным меню).
  - Произвольный текст вне диалога (`filters.TEXT & ~filters.COMMAND`) → `fallback_text_handler`.
- **Inline-кнопки (`astralio/keyboards/callbacks.py` и `astralio/keyboards/menus.py`):**
  - Общее число уникальных `callback_data` токенов в `CB` (`ALL_EXACT_CALLBACKS`): **36** (проверено скриптом).
  - Каждый токен проверен на длину ≤ 64 байт UTF-8 и на 100% покрытие зарегистрированными `CallbackQueryHandler` / `ConversationHandler` в автоматическом тесте `tests/test_callbacks_and_config.py::test_every_keyboard_button_has_valid_registered_handler` (**PASSED**).
  - Устаревшие или поддельные `callback_data` безопасно перехватываются `invalid_or_stale_callback_handler` (`astralio/handlers/common.py:108-133`) через строгий allowlist `is_valid_callback_data()`.
  - Во всех 5 пошаговых диалогах присутствуют кнопки `⬅️ Назад` (`CB.NAV_BACK`) и `✖️ Отмена` (`CB.NAV_CANCEL`) через `wizard_nav_keyboard()` (`astralio/keyboards/menus.py:187-202`).

---

## 5. Аудит реализации всех семи модулей

| № | Модуль | Файлы реализации | Подтверждённый функционал | Выявленные ограничения / заметки |
|---|---|---|---|---|
| 1 | **Регистрация и профиль** | `handlers/profile.py`, `services/user_service.py`, `services/validators.py`, `repositories/user_repository.py` | Авто-регистрация (`telegram_id`, имя, `username`), просмотр и редактирование даты, времени (`ЧЧ:ММ` или «неизвестно») и места рождения с геокодированием и таймзоной. Валидация дат (`1900-01-01` .. `today`), времени (`00:00`–`23:59`). | Эмитит `PTBUserWarning` (`per_message=False`) в `profile.py:193`. |
| 2 | **Натальная карта** | `handlers/natal.py`, `services/astrology_service.py`, `infrastructure/geocoding.py` | Расчёт по сохранённому профилю (`natal:from_profile`) или пошаговый ввод новых данных (`natal:new`). Реальный расчёт 10 планет, Асцендента, МС, 12 домов и 5 мажорных аспектов через `pyswisseph`. Явное предупреждение об ограничениях при неизвестном времени/координатах. | При неизвестном времени используется полдень UTC и дома/Асцендент не выдумываются (`astrology_service.py`). Эмитит `PTBUserWarning` (`natal.py:299`). |
| 3 | **Совместимость (Синастрия)** | `handlers/compatibility.py`, `services/compatibility_service.py` | Два режима: «Мой профиль + партнёр» (`compat:use_profile`) и ручной ввод двух человек (`compat:manual`). Сравнение 7 планет двух натальных карт (`sun..saturn`), межкартовые аспекты, баланс стихий (`_ELEMENT_COMPAT`), 5 категорий оценок и человекопонятные объяснения (`_aspect_explanation`). | Данные партнёров не сохраняются в отдельный список «Мои люди» (каждый раз вводятся заново). Эмитит `PTBUserWarning` (`compatibility.py:505`). |
| 4 | **Прогнозы** | `handlers/forecast.py`, `services/forecast_service.py` | Ежедневный (`forecast:daily`, 1 день) и недельный (`forecast:weekly`, 7 дней) прогнозы, рассчитанные по **реальным транзитам** 7 планет (`sun..saturn`) к натальным планетам и Асценденту пользователя на полдень UTC каждого дня с дедупликацией по минимальному орбу (`best_transits`). | Требует заполненной даты рождения в профиле (честно предлагает заполнить, не выдаёт случайный текст). Нет фоновых утренних рассылок. |
| 5 | **Таро** | `handlers/tarot.py`, `services/tarot_service.py`, `services/tarot_deck.py`, `repositories/reading_repository.py` | Полная колода из **78 уникальных карт** (`len(FULL_TAROT_DECK) == 78`). 4 расклада: Карта дня (1), Прошлое·Настоящее·Будущее (3), Отношения (3), Выбор пути (5). Криптостойкая выборка без повторений (`secrets.SystemRandom().sample`), вероятность перевёрнутой карты 30%, опциональный вопрос (до 300 симв.), сохранение истории и просмотр последних 5 раскладов (`tarot:history`). | 1) В `handlers/tarot.py:110` прямой доступ к приватному полю `services.tarot_service._reading_repo` и двойная запись в БД при ответе AI.<br>2) `clean_question` сохраняется уже HTML-экранированным (`handlers/tarot.py:84`).<br>3) Эмитит `PTBUserWarning` (`tarot.py:158`). |
| 6 | **Premium** | `handlers/premium.py`, `services/premium_service.py`, `repositories/payment_repository.py` | Страница тарифов (**199 ⭐ / 30 дн.**, **499 ⭐ / 90 дн.**, **1499 ⭐ / 365 дн.**, валюта `XTR`), проверка реального статуса подписки (`premium:status`), полный цикл Telegram Stars (`send_invoice` с `provider_token=""`, `PreCheckoutQueryHandler`, `SUCCESSFUL_PAYMENT`), атомарная идемпотентность в `payments/{charge_id}`. **Не имитирует оплаты.** | По умолчанию `TELEGRAM_STARS_ENABLED=False` (`config.py:51`). Пока нет реальных ограничений (paywall/feature flags) между Free и Premium в других модулях. |
| 7 | **Помощь и обратная связь** | `handlers/help.py`, `repositories/feedback_repository.py` | Подробная инструкция по всем функциям (`help:guide`) и пошаговая отправка обратной связи (`help:feedback`, валидация 5–2000 символов в `validators.py:101-108`) с сохранением в `feedback`. | Эмитит `PTBUserWarning` (`help.py:108`). |

---

## 6. Firebase, Firestore и JSON Fallback

### 6.1. Текущее состояние Firebase Admin SDK в рантайме (КРИТИЧЕСКАЯ ПРОБЛЕМА №1)
- Из логов `/api/bot-status`:
  - `hasFirebaseAdmin: true`, проект `astralis-b2fcb` (`FIREBASE_PROJECT_ID`, `FIREBASE_CLIENT_EMAIL`, `FIREBASE_PRIVATE_KEY` заданы в AI Studio Secrets).
  - При старте `create_firestore_client()` (`astralio/infrastructure/firebase.py:38-112`) падает на этапе `stage=certificate`:
    `ValueError (Failed to initialize a certificate credential. Caused by: "Could not deserialize key data...") [has_begin=True, has_end=True, key_lines=28, body_len=1624, b64_ok=True, email_ok=True]`.
  - Диагностика подтверждает: маркеры `BEGIN/END`, 28 строк и валидный алфавит Base64 присутствуют, но содержимое PEM-ключа в секрете `FIREBASE_PRIVATE_KEY` не десериализуется `cryptography` (ключ повреждён или искажён при копировании).

### 6.2. Работа JSON Fallback (`LocalFileFirestoreClient`)
- В `astralio/app.py:40-50` реализован корректный управляемый fallback:
  - При `STORAGE_MODE=auto` (по умолчанию) ошибка `FirebaseInitError` логируется как `WARNING`, и бот переключается на потокобезопасное локальное хранилище `LocalFileFirestoreClient` (`astralio/infrastructure/local_store.py`) с атомарной записью через `.tmp`-файл в `.astralio_local_db.json`.
  - При `STORAGE_MODE=firestore` (строгий режим для продакшена) `FirebaseInitError` пробрасывается наверх и аварийно останавливает старт (`main.py:42-44`). Поведение подтверждено тестом `test_storage_mode_auto_falls_back_on_invalid_firebase_key_while_firestore_is_strict` (**PASSED**).
- **Риск в AI Studio:** файл `.astralio_local_db.json` живёт внутри временного контейнера Google AI Studio и будет потерян при пересоздании контейнера.

### 6.3. Рассинхронизация двух Firebase-конфигураций в репозитории
- **Веб-часть (`firebase-applet-config.json`, `src/firebase.ts`, `firestore.rules`):** подключена к AI Studio-проекту `gen-lang-client-0054273535` (БД `ai-studio-astralio-6467cde6-a21a-4a5f-86eb-429b5e379e4a`), использует подколлекцию `users/{uid}/tarotReadings/{readingId}` (camelCase) и правила `firestore.rules` с `default deny`, проверкой `isOwner(userId)` и `isVerifiedUser()`.
- **Python-бот (`astralio/repositories/*` + Secrets):** нацелен на проект пользователя `astralis-b2fcb` (база `(default)`), использует подколлекцию `users/{telegram_id}/tarot_readings/{reading_id}` (snake_case), `payments/{charge_id}` и `feedback/{feedback_id}`.
- На работу самого бота это не влияет (Admin SDK обходит клиентские `firestore.rules`), но если в будущем потребуется единый личный кабинет веб + Telegram, схему и проект нужно унифицировать.

---

## 7. AI-интеграция (`AIService`)

- **Реализация (`astralio/services/ai_service.py`):**
  - Изолированный клиент на `httpx.AsyncClient`, вызывающий `POST {AI_BASE_URL}/chat/completions` (по умолчанию `https://api.openai.com/v1`, модель `gpt-4o-mini`, `timeout=15.0s`, `max_tokens=450`, `temperature=0.5`).
  - Встроенный per-user sliding-window rate limiter (`_allow_request`, по умолчанию 5 запросов/мин).
  - Честный fallback: при любой ошибке сети/API/таймаута/лимита возвращает `InterpretationResult(text=local_fallback, source="local_fallback", reason=...)`.
- **КРИТИЧЕСКАЯ ПРОБЛЕМА №2 (подтверждена живыми логами `/api/bot-status`):**
  - В рантайме `ai_enabled=True` (`AI_API_KEY` задан), однако **все 6 живых запросов** (`11:53:31`, `11:53:37`, `11:53:47`, `11:58:02`, `11:58:49`, `11:59:17 UTC`) завершились ошибкой:
    `WARNING | astralio.services.ai_service | AI interpretation request failed (HTTPStatusError); using local fallback`.
  - Причина: ключ в `AI_API_KEY` либо относится к другому провайдеру (например, Gemini API вместо OpenAI без переопределения `AI_BASE_URL` и `AI_MODEL`), либо отклоняется OpenAI API (`401`/`403`/`429`).
  - Недостаток наблюдаемости в `ai_service.py:144-147`: логируется только `type(exc).__name__` (`HTTPStatusError`) без `exc.response.status_code`, что затрудняет мгновенную диагностику (при этом тело ответа логировать не нужно, достаточно числового HTTP-кода).

---

## 8. Натальная карта, астрономические расчёты, Таро и совместимость

- **Астрономическая точность (`astralio/services/astrology_service.py`):**
  - Используется реальная библиотека **`pyswisseph==2.10.3.2`** (`swe.calc_ut` с флагами `swe.FLG_MOSEPH | swe.FLG_SPEED`, юлианская дата `swe.julday`).
  - Рассчитываются 10 планет (`Солнце..Плутон`), эклиптическая долгота, знак, градус/минута, скорость и флаг ретроградности (`is_retrograde`).
  - Геокодирование (`astralio/infrastructure/geocoding.py`): встроенный справочник проверенных координат и IANA-таймзон для 80+ крупных городов РФ, СНГ и мира + парсинг сырых координат (`_COORDS_RE`) + опциональный Nominatim fallback с `TimezoneFinder`.
  - Проверено 7 тестами в `tests/test_astrology_service.py` (включая реальные координаты планет, расчёт домов при известном времени, явные ограничения при неизвестном времени и смену часовых поясов).
- **Таро и совместимость:**
  - `TarotService` (`astralio/services/tarot_service.py`): 78 карт (22 Старших + 56 Младших Арканов в `tarot_deck.py`), выборка `secrets.SystemRandom().sample` гарантирует отсутствие дубликатов. Проверено 4 тестами в `tests/test_tarot_service.py`.
  - `CompatibilityService` (`astralio/services/compatibility_service.py`): строит две реальные натальные карты и вычисляет межпланетные аспекты (`MAJOR_ASPECTS`), баланс стихий и итоговый отчёт. Проверено 2 тестами в `tests/test_compatibility_service.py`.
  - `ForecastService` (`astralio/services/forecast_service.py`): вычисляет реальные транзиты к наталу на 1 или 7 дней. Проверено 2 тестами в `tests/test_forecast_service.py`.

---

## 9. Безопасность

| Аспект | Реализация и доказательство | Оценка |
|---|---|---|
| **Защита секретов в логах** | `SecretRedactionFilter` (`astralio/infrastructure/logging.py:17-46`) вырезает `BOT_TOKEN`, PEM-ключи, `Bearer`-токены и все секреты из `Settings.secret_values()`. `httpx`/`httpcore` переведены на уровень `WARNING` (`logging.py:67-68`). В `server.ts:11-20` продублирована фильтрация `redactSecrets()`. Проверено тестом `test_secret_redaction_filter_masks_tokens_and_keys`. | **Высокая** |
| **Защита от подделки `callback_data`** | Строгий allowlist из 36 токенов в `astralio/keyboards/callbacks.py:69-73`. | **Высокая** |
| **Защита от XSS / HTML-инъекций в Telegram** | Экранирование пользовательских строк через `escape_html()` (`astralio/handlers/deps.py`) в приветствии, вопросах Таро и ответах AI. | **Хорошая** |
| **Безопасность платежей Stars** | Невозможно активировать Premium без реального `telegram_payment_charge_id`; проверка `currency == "XTR"`, `payload_user_id == telegram_id`, суммы тарифа и атомарная запись `doc_ref.create` в `payments/{charge_id}` (`PaymentRepository.record_payment_idempotent`). Проверено 3 тестами в `tests/test_premium_service.py`. | **Высокая** |
| **Клиентские правила Firestore** | `firestore.rules` (234 строки): `default deny`, валидация схем, запрет `list` на `/users`, проверка `isOwner` и `isVerifiedUser`. | **Высокая** |
| **Валидация пользовательского ввода** | Строгие парсеры дат, времени, имён (2–60 симв.) и фидбека (5–2000 симв.) в `astralio/services/validators.py`. | **Высокая** |

---

## 10. Тесты и качество кода (фактический прогон `2026-11-21`)

- **Линтер и форматирование:**
  - `.venv/bin/ruff check astralio tests` → **`All checks passed!`** (0 ошибок).
  - `.venv/bin/ruff format --check astralio tests` → **`54 files already formatted`** (0 расхождений).
- **Автотесты (`.venv/bin/pytest -v`):** **`41 passed in 0.71s`** (100% зелёный прогон):
  - `tests/test_ai_service.py` — 4 passed
  - `tests/test_astrology_service.py` — 7 passed
  - `tests/test_callbacks_and_config.py` — 5 passed
  - `tests/test_compatibility_service.py` — 2 passed
  - `tests/test_forecast_service.py` — 2 passed
  - `tests/test_handlers.py` — 9 passed
  - `tests/test_premium_service.py` — 3 passed
  - `tests/test_repositories.py` — 5 passed
  - `tests/test_tarot_service.py` — 4 passed
- **CI/CD:** настроен `.github/workflows/ci.yml` для автоматического прогона проверок.

---

## 11. Критические ошибки и риски

1. **[CRITICAL] Невалидный `FIREBASE_PRIVATE_KEY` в секретах для `astralis-b2fcb`:**
   - *Доказательство:* лог запуска `/api/bot-status` — `ValueError: Could not deserialize key data` на `stage=certificate`.
   - *Влияние:* бот не пишет данные в облачный Firestore и вынужденно использует локальный JSON-файл `.astralio_local_db.json`.
2. **[CRITICAL] 100% отказов внешнего AI-провайдера в живом рантайме (`HTTPStatusError`):**
   - *Доказательство:* 6 подряд предупреждений `AI interpretation request failed (HTTPStatusError); using local fallback` в логах `/api/bot-status` (`11:53–11:59 UTC`).
   - *Влияние:* хотя `AI_API_KEY` задан, пользователи фактически получают локальные детерминированные шаблоны вместо AI-интерпретаций, а каждый запрос теряет время на неудачный HTTP-вызов.
3. **[CRITICAL — инфраструктурный] Временная среда Google AI Studio не обеспечивает работу 24/7:**
   - *Доказательство:* бот запущен как дочерний процесс `tsx server.ts` в превью-контейнере, который останавливается после закрытия вкладки/таймаута неактивности.
4. **[MEDIUM] Незавершённость коммерческого контура Premium:**
   - `TELEGRAM_STARS_ENABLED=False` и отсутствие разграничения Free/Premium-лимитов в обработчиках (оплата подготовлена, но не монетизирует трафик).
5. **[LOW] Технический долг в коде:**
   - 5 предупреждений `PTBUserWarning` (`per_message=False`) при старте.
   - Прямой доступ к `_reading_repo` и двойная запись расклада Таро при активном AI (`astralio/handlers/tarot.py:110`).
   - Рассинхронизация Firebase-проектов и имён подколлекций (`tarot_readings` vs `tarotReadings`) между ботом и веб-интерфейсом.

---

## 12. Итоговая оценка готовности к запуску

| Критерий | Готовность | Комментарий |
|---|---|---|
| Кодовая база, архитектура, 7 модулей и тесты | **9 / 10 (Готово к MVP)** | Все 7 модулей работают, 36/36 кнопок покрыты, 41/41 тест зелёный, `pyswisseph` и 78 карт Таро работают корректно. |
| Локальный запуск и тестирование в Google AI Studio | **8 / 10 (Работает сейчас)** | `@Astraliio_bot` онлайн, отвечает пользователям на `/start` и все разделы через локальный JSON fallback. |
| Боевой продакшен 24/7 для реальных пользователей | **5 / 10 (Условно готово — требуется 3 шага)** | Необходимо: (1) заменить `FIREBASE_PRIVATE_KEY` на валидный JSON-ключ из Firebase Console, (2) починить связку `AI_API_KEY` / `AI_BASE_URL` / `AI_MODEL`, (3) выкатить воркер по `Procfile` на постоянный хостинг (Railway / Fly.io / VPS) с `STORAGE_MODE=firestore`. |
