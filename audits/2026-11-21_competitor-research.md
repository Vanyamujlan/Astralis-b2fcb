# ГЛУБОКОЕ ИССЛЕДОВАНИЕ КОНКУРЕНТОВ ASTRALIO — ТОЛЬКО TELEGRAM

**Дата проведения:** `2026-11-21`  
**Версия Astralio на момент аудита:** `0.1.0` (MVP, `@Astraliio_bot`)  
**Статус документа:** Полная сохранённая версия (Этап 1 + Дополнение 26–29 + Этап 2: проверка достоверности).  
**Важное методологическое примечание:** Настоящий файл содержит **полный несокращённый текст Этапа 1** (раздел I), **Дополнение по ботам №26–29** (раздел II) и **полный аудит достоверности Этапа 2** (раздел III), где все неподтверждённые данные, рыночные гипотезы и неточности Этапа 1 явно обозначены и исправлены.

---

# РАЗДЕЛ I. ЭТАП 1 — ПЕРВИЧНОЕ ИССЛЕДОВАНИЕ РЫНКА TELEGRAM-КОНКУРЕНТОВ ASTRALIO (2026)

> **Методология и прозрачность проверки:**
> 1. **Прямая проверка `https://t.me/<username>`:** все 25 ботов из отчёта проверены прямыми HTTP-запросами к их карточкам в Telegram (`t.me`), подтверждено существование `username`, актуальный `Title`, `Bio/Description`, контакты поддержки и привязанные оферты/лендинги.
> 2. **Ограничение среды выполнения (Bot API vs User Client):** из серверного контейнера без персонального пользовательского аккаунта (MTProto userbot) невозможно отправить `/start` *в чужого бота* (в Telegram Bot API боты не могут писать другим ботам). Поэтому там, где внутреннее меню, тарифная сетка, механика Stars/кристаллов и экранные флоу подтверждены через официальные публичные оферты, политики конфиденциальности, веб-лендинги самих ботов (`superastro.ru`, `astrotay.ru`, `fate-whisper.ru`, `arcana.guru`, `teletype.in/@tarotnatalbot/legaldoc`) и верифицированные профили аналитических платформ (`minitelegram.com`, `grambots.com`, `tlg.me`), это явно указано со ссылками. Там, где закрытый внутренний paywall доступен только из личного Telegram-клиента после `/start`, это честно отмечено.

---

## 1. СПИСОК И РЕАЛЬНАЯ ПРОВЕРКА 25 TELEGRAM-КОНКУРЕНТОВ

Ниже представлены **14 ботов из стартового списка** (все 14 реально существуют в Telegram) + **11 дополнительных сильных Telegram-ботов и Mini Apps** в нишах натальных карт, ИИ-астрологии, Таро, совместимости и Матрицы судьбы.

### Часть А. Проверка 14 ботов из обязательного списка

#### 1. `@SuperTarologBot` — **Super Astro (Эзотерика, Таро, Астрология, Натальная карта)**
* **Ссылки:** [https://t.me/SuperTarologBot](https://t.me/SuperTarologBot) | Официальный сайт и документация бота: [https://superastro.ru](https://superastro.ru) | Оферта: [https://superastro.ru/oferta](https://superastro.ru/oferta) | Правила оплаты: [https://superastro.ru/oplata-i-vozvrat](https://superastro.ru/oplata-i-vozvrat) | Канал: [https://t.me/s/superastro_ru](https://t.me/s/superastro_ru)
* **Статус:** Активен (чат-бот + полноценное Telegram Mini App).
* **Меню и сценарий (`/start`):** после `/start` бот сразу присылает «Карту дня» и предлагает ввести дату рождения (первый расчёт без регистрации). Из чата открывается как текстовое меню, так и встроенное Telegram Mini App.
* **Реально работающие функции (по официальному сайту и оферте):**
  * Натальная карта (120 положений планет в знаках, 12 домов, Асцендент, аспекты; если время неизвестно — считает космограмму без домов с возможностью дозаполнить время позже).
  * Ежедневный прогноз именно **по транзитам к натальной карте** (а не общий по знаку Солнца).
  * Таро (колода Райдера-Уэйта 78 карт + малый оракул Ленорман 36 карт, 25 раскладов с позициями).
  * Матрица судьбы (22 энергии, 7 позиций схемы Ладини: центр, деньги, отношения, род) и квадрат Пифагора.
  * Совместимость (по знакам бесплатно, синастрия по двум натальным картам — в Mini App) + AI-чат с астрологом.
* **Бесплатные лимиты:** карта дня, базовый расчёт натальной карты и гороскоп бесплатны; **каждый день начисляются бесплатные «кристаллы»**, которые можно тратить на премиум-функции.
* **Цены и Telegram Stars:** гибридная монетизация — покупка пакетов «кристаллов» и подписок через **Telegram Stars** и **ЮKassa** (карты РФ/МИР).
* **Наличие AI:** да (LLM генерирует персональные разборы поверх астрологической базы редакции).
* **Запрашиваемые данные (по Политике ПД):** `Telegram ID`, `username`, имя, дата, время и место рождения, история раскладов и текстовые вопросы к ИИ.

#### 2. `@tarotnatalbot` — **Таролог — Расклады Гадание**
* **Ссылки:** [https://t.me/tarotnatalbot](https://t.me/tarotnatalbot) | Юридическая оферта бота: [https://teletype.in/@tarotnatalbot/legaldoc](https://teletype.in/@tarotnatalbot/legaldoc) | Аналитика Grambots: [https://www.grambots.com/ru/bots/tarotnatalbot](https://www.grambots.com/ru/bots/tarotnatalbot) | Аналитика MiniTelegram: [https://minitelegram.com/ru/apps/tarotnatalbot](https://minitelegram.com/ru/apps/tarotnatalbot)
* **Статус:** Активен. Крупнейший по трафику бот в проиндексированной выборке трекеров (744,3 тыс. MAU на 20.11.2026 по MiniTelegram / 1,079 млн MAU на Grambots). Поддержка: `@astroaibot_support`.
* **Меню и сценарий (`/start`):** на старте короткий онбординг из 3 шагов (имя, дата рождения для определения знака зодиака, выбор колоды — Райдер-Уэйт или Марсельское Таро). Поддерживает 7 языков.
* **Реально работающие функции:**
  * Расклад на вопрос (3 карты), «Да / Нет» (1 карта для себя или другого человека), «Отношения», «Карта дня», «Месяц вперёд».
  * Глубокие расклады («Кельтский крест», «Год вперёд»).
  * Диалоговый режим: после расклада можно задать уточняющие вопросы ИИ или вытянуть доп. карту.
  * История раскладов и геймифицированное «Колесо фортуны» (подтверждено в п. 4 оферты).
* **Бесплатные лимиты:** на старте выдаётся **3 бесплатных кредита + бесплатная Карта дня** + бонусы из «Колеса фортуны».
* **Цены и Telegram Stars:** система кредитов + Premium-подписка (открывает «Кельтский крест», «Год вперёд» и доп. карты). Оплата через **Telegram Stars** и **ЮKassa** (п. 6 оферты).
* **Наличие AI:** да (явно декларируется в п. 5 оферты «Условия использования ИИ-функций»).
* **Запрашиваемые данные:** `Telegram ID`, имя, дата рождения (знак зодиака), текстовые вопросы, подтверждение 18+.

#### 3. `@arcanagurubot` — **Аркана – Таролог с искусственным интеллектом**
* **Ссылки:** [https://t.me/arcanagurubot](https://t.me/arcanagurubot) | Веб-лендинг: [https://arcana.guru](https://arcana.guru) | Профиль Grambots: [https://www.grambots.com/ru/bots/arcanagurubot](https://www.grambots.com/ru/bots/arcanagurubot) | Профиль MiniTelegram: [https://minitelegram.com/ru/apps/arcanagurubot](https://minitelegram.com/ru/apps/arcanagurubot)
* **Статус:** Активен (чат-бот + Telegram Mini App, 18 языков интерфейса). Поддержка: `@ArcanaSupportBot`.
* **Меню и сценарий (`/start`):** **нулевой онбординг (без анкет)** — после `/start` пользователь сразу пишет вопрос обычным языком.
* **Реально работающие функции:**
  * Автоматический подбор схемы и расклад карт под вопрос в свободной форме с генерацией картинки расклада.
  * **Распознавание фото физических карт:** пользователь может сфотографировать свой реальный расклад или прислать список арканов — ИИ связывает карты в единый разбор.
  * Уточняющие вопросы в формате живого диалога, выбор колоды, «Совет дня» в Mini App.
* **Бесплатные лимиты:** бесплатный стартовый диалог и ежедневный «Совет дня» в Mini App; далее лимит запросов.
* **Цены и Telegram Stars:** оплата пакетов раскладов и подписки внутри бота/Mini App *(точные цены и платёжные шлюзы снаружи не опубликованы — см. Раздел III)*.
* **Наличие AI:** да (LLM + мультимодальное распознавание фото раскладов).
* **Запрашиваемые данные:** не требует анкеты рождения на старте (анонимный вход по `Telegram ID` + текст/фото вопроса).

#### 4. `@astrotaybot` — **Астро Тэй (AstroTay AI)**
* **Ссылки:** [https://t.me/astrotaybot](https://t.me/astrotaybot) | Официальный сайт бота: [https://astrotay.ru](https://astrotay.ru)
* **Статус:** Активен. Поддержка: `@phenikstay`.
* **Меню и сценарий (`/start`):** после `/start` просит заполнить единый профиль рождения (дата, время, место рождения), после чего открывает меню из **8 эзотерических практик**.
* **Реально работающие функции (по официальному сайту `astrotay.ru`):**
  1. Астрология (натальная карта + персональный гороскоп по дате, времени и месту).
  2. **Релокационная астрология** (ТОП-3 лучших города для денег, любви и здоровья + чего избегать по натальной карте).
  3. Таро (расклады на ситуацию, отношения и будущее с трактовкой ИИ).
  4. Матрица Судьбы (энергии, предназначение, совместимость).
  5. Нумерология (числа судьбы, личный год, жизненные циклы по дате и имени).
  6. **Сюцай** (цифровая психология по дате рождения).
  7. **Хиромантия по фото** (чтение линий ладони через Computer Vision/LLM).
  8. **Сонник по Юнгу** (толкование снов через архетипы и тень).
* **Бесплатные лимиты:** «Бесплатный старт» (первый базовый расчёт бесплатно за 1 минуту).
* **Цены и Telegram Stars:** платные глубокие разборы и подписка *(внутренний прайс закрыт за онбордингом внутри Telegram-клиента; конкретные суммы и способ оплаты снаружи не подтверждены)*.
* **Наличие AI:** да (текстовая LLM + мультимодальный анализ фото ладони).
* **Запрашиваемые данные:** `Telegram ID`, имя, дата, время, место рождения, фото ладони (для хиромантии).

#### 5. `@esotero_bot` — **🔮 Esotero — астрология и прогнозы** `[НЕ ПОДТВЕРЖДЁН ВНЕШНИМИ ИСТОЧНИКАМИ — КАТЕГОРИЯ B]`
* **Ссылки:** [https://t.me/esotero_bot](https://t.me/esotero_bot)
* **Статус:** Аккаунт в `t.me` существует. Поддержка и коммерческие предложения: `@genbooking`.
* **Проверка и функционал:** позиционируется в Bio как бот персональных гороскопов, астропрогнозов и чата. Публичного веб-лендинга и внешней оферты нет; детальное меню и цены доступны только при интерактивном входе с личного Telegram-аккаунта.

#### 6. `@LunairaBot` — **Lunaira (Персональная астрология и AI-астролог LUNA)** `[НЕ ПОДТВЕРЖДЁН ВНЕШНИМИ ИСТОЧНИКАМИ — КАТЕГОРИЯ B]`
* **Ссылки:** [https://t.me/LunairaBot](https://t.me/LunairaBot)
* **Статус:** Аккаунт в `t.me` существует.
* **Проверка и функционал (по Bio `t.me`):** заявлены 5 ключевых модулей: Натальная карта, AI-астролог LUNA, Совместимость, Таро и Ежедневный гороскоп. Внутренний интерфейс и прайс в Stars снаружи не проверены.

#### 7. `@smartytoolsbot` — **SmartyToolsBot**
* **Ссылки:** [https://t.me/smartytoolsbot](https://t.me/smartytoolsbot) | Описание в каталоге: `tlg.me` (проверено через веб-индекс)
* **Статус:** Активен.
* **Заявленные и подтверждённые каталогом функции:** мульти-комбайн:
  * Натальная карта с домами и аспектами, синастрия (совместимость), **Соляр (годовой прогноз с датами транзитов)**.
  * Матрица судьбы и нумерология.
  * Таро Райдера-Уэйта, **Руны Старшего Футарка**, оракул «Да/Нет».
  * Лунный календарь вплоть до 2055 года, лунные ритуалы, сонник.
  * **Формат выдачи:** быстрые ответы прямо в чате либо **скачиваемые подробные PDF-разборы**.
* **Цены и Telegram Stars:** подтверждена оплата расширенных разборов и PDF-отчётов через **Telegram Stars** *(без указания точной суммы в открытом каталоге)*.
* **Запрашиваемые данные:** дата, время и город рождения (для натала, соляра и синастрии).

#### 8. `@oracul_tarot_bot` — **Oracul — Tarot, Astrology & Numerology**
* **Ссылки:** [https://t.me/oracul_tarot_bot](https://t.me/oracul_tarot_bot) | Профиль и статистика MiniTelegram: [https://minitelegram.com/ru/apps/oracul_tarot_bot](https://minitelegram.com/ru/apps/oracul_tarot_bot)
* **Статус:** Активен (чат-бот + Telegram Mini App; **1,5 тыс. MAU, рост +38,5% за 30 дней**, срез `20.11.2026`).
* **Меню и сценарий (`/start`):** мультиязычный интерфейс (RU/EN). Слоган в описании `t.me`: *«Ask your question — your first readings are free 🎁»*.
* **Функции (по MiniTelegram):**
  * Таро-расклады под конкретный вопрос пользователя в формате чата.
  * «Астрологический портрет» по натальной карте и расчёт Матрицы судьбы.
  * Отдельный модуль совместимости по натальным данным.
  * **Интерпретация по фото:** загрузка изображений уже построенных схем и раскладов карт для расшифровки.
* **Бесплатные лимиты:** первые расклады после `/start` бесплатны (приветственный бонус).

#### 9. `@OracleAstro_Bot` — **🔮 Совместимость • Натальная Карта • Таро • Гороскоп («Безмолвный Оракул»)**
* **Ссылки:** [https://t.me/OracleAstro_Bot](https://t.me/OracleAstro_Bot) | Профиль и статистика MiniTelegram: [https://minitelegram.com/ru/apps/OracleAstro_Bot](https://minitelegram.com/ru/apps/OracleAstro_Bot)
* **Статус:** Активен (27 MAU по данным MiniTelegram, срез `20.09.2026`).
* **Функции:** несмотря на заголовок в `t.me` («Совместимость • Натальная Карта • Таро • Гороскоп»), по результатам обзора MiniTelegram сервис представляет собой **художественно-мистический ИИ-оракул («Безмолвный Оракул🎇»)**, который отвечает на вопросы в свободной форме в стиле древних свитков и пророчеств, **не выполняя строгих астрономических расчётов эфемерид**.

#### 10. `@Natalchart1_bot` — **Натальная карта и Таро** `[НЕ ПОДТВЕРЖДЁН ВНЕШНИМИ ИСТОЧНИКАМИ — КАТЕГОРИЯ B]`
* **Ссылки:** [https://t.me/Natalchart1_bot](https://t.me/Natalchart1_bot)
* **Статус:** Аккаунт в `t.me` существует. Описание: *«🔮 Узнай свою натальную карту, сделай расклад Таро и расчитай нумерологию в один клик!»*. Внутренний функционал и тарифы снаружи не проверены.

#### 11. `@tarolog_astro_bot` — **ИИ Таролог — Натальная карта** `[НЕ ПОДТВЕРЖДЁН ВНЕШНИМИ ИСТОЧНИКАМИ — КАТЕГОРИЯ B]`
* **Ссылки:** [https://t.me/tarolog_astro_bot](https://t.me/tarolog_astro_bot)
* **Статус:** Аккаунт в `t.me` существует. Контакт владельца в Bio: `@TylerDurdenBoy`. Описание: *«🔮 ИИ читает Таро, строит натальную карту и совместимость по звёздам»*. Функционал снаружи не проверен.

#### 12. `@smart_zodiac_bot` — **Smart Zodiac** `[НЕ ПОДТВЕРЖДЁН ВНЕШНИМИ ИСТОЧНИКАМИ — КАТЕГОРИЯ B]`
* **Ссылки:** [https://t.me/smart_zodiac_bot](https://t.me/smart_zodiac_bot)
* **Статус:** Аккаунт в `t.me` существует. Описание: *«🔮 Персональный астробот: гороскоп дня, Таро, совместимость и натальная карта»*. Функционал снаружи не проверен.

#### 13. `@astromoon_ai_bot` — **AstroBot (AI-астролог)** `[НЕ ПОДТВЕРЖДЁН ВНЕШНИМИ ИСТОЧНИКАМИ — КАТЕГОРИЯ B]`
* **Ссылки:** [https://t.me/astromoon_ai_bot](https://t.me/astromoon_ai_bot) | Привязанный канал/аккаунт: [https://t.me/astromoon_ai](https://t.me/astromoon_ai)
* **Статус:** Аккаунт в `t.me` существует. Описание: *«✨ AI-астролог: натальная карта, совместимость, прогнозы, карта дня таро. Канал: @astromoon_ai»*. Функционал снаружи не проверен.

#### 14. `@mystaramagicbot` — **Mystara** `[НЕ ПОДТВЕРЖДЁН ВНЕШНИМИ ИСТОЧНИКАМИ — КАТЕГОРИЯ B]`
* **Ссылки:** [https://t.me/mystaramagicbot](https://t.me/mystaramagicbot)
* **Статус:** Аккаунт в `t.me` существует. Описание: *«Астрология и Таро персонально для тебя. Гороскоп, совместимость, натальная карта»*. Функционал снаружи не проверен.

---

### Часть Б. 11 дополнительных верифицированных Telegram-конкурентов (сверх стартового списка)

#### 15. `@fate_whisper_bot` — **Fate Whisper ✧ Таро-Бот**
* **Ссылки:** [https://t.me/fate_whisper_bot](https://t.me/fate_whisper_bot) | Официальный сайт: [https://fate-whisper.ru](https://fate-whisper.ru) | Правила и Stars-монетизация: [https://fate-whisper.ru/terms](https://fate-whisper.ru/terms) | Политика данных (полная схема БД бота): [https://fate-whisper.ru/privacy](https://fate-whisper.ru/privacy) | Канал: [https://t.me/s/fate_whisper_tarot](https://t.me/s/fate_whisper_tarot)
* **Статус:** Активен. Эталон геймификации и удержания (Retention) в Telegram.
* **Функции (подтверждены сайтом и Политикой ПД):**
  * 8 раскладов Таро (от 1 до 10 карт: Карта дня, Да/Нет, Карьера, Мудрость, Свой вопрос на 3 карты, Выбор на 5 карт, Три времени на 7 карт, Отношения на 7 карт, Кельтский крест на 10 карт).
  * Натальная карта (планеты, аспекты, стихии, транзиты), Совместимость знаков, Гороскопы (день/завтра/неделя/месяц).
  * **«Звёздный паспорт»** по дате рождения (знак, стихия, планета, китайский гороскоп, число пути, цвет ауры, лунная фаза и аркан Таро рождения).
  * **Геймификация:** **Коллекция из 78 карт Таро**, **Квесты и награды**, **Серия посещений (Streak 7 дней — награда на 7-й день)**, реферальная система.
* **Цены и Telegram Stars:** монетизация **исключительно через Telegram Stars** (п. 5.1 Условий использования: подписки, отдельные расклады и пакеты; конкретные суммы в ⭐ на сайте не опубликованы).

#### 16. `@taro_gpt_bot` — **Таролог (TaroGPT)**
* **Ссылки:** [https://t.me/taro_gpt_bot](https://t.me/taro_gpt_bot) | Сайт и оферта: [https://tarogpt.ru](https://tarogpt.ru), [https://tarogpt.ru/legal/tarobot-terms](https://tarogpt.ru/legal/tarobot-terms) | Профиль MiniTelegram: [https://minitelegram.com/ru/apps/taro_gpt_bot](https://minitelegram.com/ru/apps/taro_gpt_bot) | Grambots: [https://www.grambots.com/ru/bots/taro_gpt_bot](https://www.grambots.com/ru/bots/taro_gpt_bot)
* **Статус:** Активен (**29,4 тыс. MAU, рост +5,8% за 30 дней**, срез `20.11.2026`; Grambots — **33 196 MAU**).
* **Функции:** специализированный ИИ-помощник для трактовки раскладов Таро **до 12 карт**, **выбор из 7 стилей трактовки**, учёт прямых и перевёрнутых карт, работа как с виртуальной колодой, так и со своей физической колодой + режим обучения Таро. Оплата подписки через **ЮMoney** (`/premium`), реферальные промокоды (п. 5.9 оферты).

#### 17. `@tarolog10_bot` — **Таролог | Таро Расклады**
* **Ссылки:** [https://t.me/tarolog10_bot](https://t.me/tarolog10_bot) | Профиль MiniTelegram: [https://minitelegram.com/ru/apps/tarolog10_bot](https://minitelegram.com/ru/apps/tarolog10_bot) | Grambots: [https://www.grambots.com/ru/bots/tarolog10_bot](https://www.grambots.com/ru/bots/tarolog10_bot)
* **Статус:** Активен (чат-бот + Telegram Mini App; **46,4 тыс. MAU, рост +44,5% за 30 дней**, срез `20.11.2026`; Grambots от `04.07.2026` — **247 886 MAU**).
* **Функции:** гибридное Mini App без обязательной регистрации — встроенный генератор веб-карт + ручной ввод выпавших карт из реальной колоды (с поддержкой перевёрнутых карт) для ИИ-расшифровки.

#### 18. `@gadalka_topbot` — **💙 Ежедневный гороскоп 💙**
* **Ссылки:** [https://t.me/gadalka_topbot](https://t.me/gadalka_topbot) | Профиль MiniTelegram: [https://minitelegram.com/ru/apps/gadalka_topbot](https://minitelegram.com/ru/apps/gadalka_topbot)
* **Статус:** Активен (**26,4 тыс. MAU, рост +8,5% за 30 дней**, срез `21.11.2026`).
* **Функции:** ежедневный гороскоп, восточный гороскоп (карьера, здоровье, отношения), совместимость в паре, расклады Таро и числовая магия.

#### 19. `@horoscopesoflovebot` — **TAROT Daily Readings 👌**
* **Ссылки:** [https://t.me/horoscopesoflovebot](https://t.me/horoscopesoflovebot) | Профиль MiniTelegram: [https://minitelegram.com/ru/apps/horoscopesoflovebot](https://minitelegram.com/ru/apps/horoscopesoflovebot)
* **Статус:** Активен (Telegram Mini App; **19,6 тыс. MAU, динамика -10,2% за 30 дней**, срез `21.11.2026`).
* **Функции:** автоматизированные расклады Таро внутри Mini App по кнопке «Задать вопрос» (виртуальная или своя колода) с позиционным разбором.

#### 20. `@milanatarba_newbot` — **Прогноз | Милана Тарба** `[КАТЕГОРИЯ C — ПУСТОЙ ПРОФИЛЬ T.ME]`
* **Ссылки:** [https://t.me/milanatarba_newbot](https://t.me/milanatarba_newbot) | Профиль MiniTelegram: [https://minitelegram.com/ru/apps/milanatarba_newbot](https://minitelegram.com/ru/apps/milanatarba_newbot)
* **Статус:** Аккаунт существует (**16,0 тыс. MAU, рост +27,9% за 30 дней**, срез `19.11.2026`), но описание `t.me` пустое.
* **Функции (по MiniTelegram):** расчёт персональных «ключей жизни» (нумерология/матрица/астропсихология) по дате рождения с фокусом на деньги, отношения и предназначение.

#### 21. `@nocturnabot_rubot` — **Ночная карта · Таро и прогнозы** `[КАТЕГОРИЯ B]`
* **Ссылки:** [https://t.me/nocturnabot_rubot](https://t.me/nocturnabot_rubot)
* **Статус:** Аккаунт в `t.me` существует.
* **Заявленные функции:** натальная карта по дате рождения и городу, карта дня, расклады Таро, прогноз по знаку зодиака, гадание на кофейной гуще и свечной маг. Базовая часть бесплатная, глубокие расклады за **Telegram Stars** *(точные цены не опубликованы)*.

#### 22. `@NatalChartRobot` — **🔮 Натальная карта – расчет и расшифровка**
* **Ссылки:** [https://t.me/NatalChartRobot](https://t.me/NatalChartRobot) | Профиль MiniTelegram: [https://minitelegram.com/ru/apps/NatalChartRobot](https://minitelegram.com/ru/apps/NatalChartRobot)
* **Статус:** Активен (Telegram Mini App, **54 MAU**, срез `28.09.2026`).
* **Функции:** расчёт натальной карты по дате, времени и месту рождения (Солнце, Луна, планеты, дома, аспекты) по блокам («общая характеристика», «личные качества», «карьера», «отношения»), **экспорт карты в PDF** и шеринг в чате.

#### 23. `@taroluxebot` — **Таро Люкс**
* **Ссылки:** [https://t.me/taroluxebot](https://t.me/taroluxebot) | Профиль MiniTelegram: [https://minitelegram.com/ru/apps/taroluxebot](https://minitelegram.com/ru/apps/taroluxebot)
* **Статус:** Активен (чат-бот + Mini App; **4,5 тыс. MAU**, -3,3%, срез `21.11.2026`).
* **Функции:** анонимные расклады Таро на произвольный вопрос, расклад на совместимость/отношения, «Да/Нет», расклад на сегодня; есть бесплатный стартовый расклад.

#### 24. `@starsvoice_bot` — **🔮 Тарологи | Расклады Таро | Гороскопы (StarsVoice)**
* **Ссылки:** [https://t.me/starsvoice_bot](https://t.me/starsvoice_bot) | Профиль MiniTelegram: [https://minitelegram.com/ru/apps/starsvoice_bot](https://minitelegram.com/ru/apps/starsvoice_bot)
* **Статус:** Активен (**2,4 тыс. MAU, рост +1,7%**, срез `20.11.2026`).
* **Функции:** мульти-персонажный бот («нейро-тарологи», имитирующие стиль разных консультантов) + подписка на персональную гороскопическую рассылку.

#### 25. `@taroshenka_bot` (555–586 MAU) и `@quantomant_bot` (541 MAU, рост +117,3%)
* **Ссылки:** [https://t.me/taroshenka_bot](https://t.me/taroshenka_bot) ([MiniTelegram](https://minitelegram.com/ru/apps/taroshenka_bot)) и [https://t.me/quantomant_bot](https://t.me/quantomant_bot) ([MiniTelegram](https://minitelegram.com/ru/apps/quantomant_bot))
* **Ключевые находки:**
  * `@taroshenka_bot` объединяет Таро, натальную карту по дате/времени/месту, персональные транзиты, соляр на год и бесплатный лунный календарь.
  * `@quantomant_bot` («ИИ-гадалка Аглая») при трактовке расклада Таро автоматически учитывает **знак зодиака, дату рождения, текущую фазу Луны и фазу Луны в ночь рождения пользователя**. На старте дарит кристаллы на 3 бесплатных расклада + ежедневную бесплатную карту дня.

---

# РАЗДЕЛ II. ДОПОЛНЕНИЕ К ЭТАПУ 1 — 4 ПРЯМЫХ АРХИТЕКТУРНЫХ КОНКУРЕНТА (№26–29)

#### 26. `@apluna_bot` — **LUNA (Натальная карта, Таро, ежедневный прогноз)**
* **Ссылки:** [https://t.me/apluna_bot](https://t.me/apluna_bot) | Профиль и статистика MiniTelegram: [https://minitelegram.com/ru/apps/apluna_bot](https://minitelegram.com/ru/apps/apluna_bot)
* **Подтверждённая аудитория:** **50 400 MAU** (срез `09.11.2026`).
* **Функции:** натальная карта, Матрица судьбы, расклады Таро, ежедневный прогноз по натальной карте, хиромантия по фото ладони + **«Разбор переписки с точки зрения чувств собеседника»**. Первый разбор по дате рождения бесплатный.

#### 27. `@mystic_companion_bot` — **Mystic Companion · Tarot**
* **Ссылки:** [https://t.me/mystic_companion_bot](https://t.me/mystic_companion_bot) | Профиль MiniTelegram: [https://minitelegram.com/ru/apps/mystic-companion-tarot](https://minitelegram.com/ru/apps/mystic-companion-tarot)
* **Формат:** Telegram Mini App.
* **Функции:**
  * **«Карта дня по твоей натальной карте и сегодняшней фазе Луны»**.
  * Натальная карта (планеты, дома, аспекты, доминирующие стихии) + **скачиваемый PDF-отчёт**.
  * Синастрия двух людей по натальным картам (кросс-аспекты).
  * Авторская колода 78 карт Райдера-Уэйта в стиле Art-Nouveau (тёмный фон, золотая филигрань), 13 раскладов + «AI-Мастер в Комнате Мастера» и нумерология.

#### 28. `@celestifyBot` — **Celestify (Персональные PDF-разборы за Telegram Stars)**
* **Ссылки:** [https://t.me/celestifyBot](https://t.me/celestifyBot) | Официальный сайт: [https://celestify.me](https://celestify.me) | Профиль MiniTelegram: [https://minitelegram.com/ru/apps/celestifybot](https://minitelegram.com/ru/apps/celestifybot)
* **Подтверждённая аудитория:** **184 MAU** (срез `22.09.2026`).
* **Бизнес-модель и точный прайс (подтверждён на `celestify.me`):**
  1. Натальная карта (эфемериды NASA JPL Horizons, ~5 стр. PDF) — **59 ⭐** (`/natal`).
  2. Ведическая нумерология и совместимость (~6 стр. PDF) — **59 ⭐** (`/numerology`).
  3. Астрологический прогноз на месяц/год (~2 стр. PDF) — **59 ⭐** (`/horoscope`).
  4. Астрокартография (~3 стр. PDF) — **59 ⭐** (`/astrocartography`).
  5. Пакет «Все 4 разбора одним платежом» — **179 ⭐** (выгода 57 ⭐).

#### 29. `@astroluminary_bot` (**AstroLuminary**) `[КАТЕГОРИЯ C — БИТАЯ ССЫЛКА В КАТАЛОГЕ]`
* **Ссылки:** [https://t.me/astroluminary_bot](https://t.me/astroluminary_bot) | Профиль MiniTelegram: [https://minitelegram.com/ru/apps/astroluminary](https://minitelegram.com/ru/apps/astroluminary)
* **Функции:** расчёт планет по эфемеридам (дата, время, место рождения), дома, ежедневный транзитный прогноз, синастрия по двум картам, AI-астролог, Таро и Матрица судьбы.
* **Модель конверсии (по MiniTelegram / `t.me`):** первый прогноз бесплатно; пробный доступ **7 дней за 1 ₽**.

---

### Примечание о гипотезах Этапа 1 (явно отделены от проверенных фактов)

> ⚠️ **Важно (неподтверждённые/оценочные элементы Этапа 1):**
> 1. Таблица «типичных рыночных диапазонов Telegram Stars» из первоначального черновика Этапа 1 (`15–49 ⭐` за 1 вопрос, `75–150 ⭐` за расклад, `150–450 ⭐` за 30 дней) являлась **аналитической рыночной оценкой**, а не выпиской из прайс-листов конкретных ботов. Документально подтверждённые цены приведены в Разделе III (§3).
> 2. Утверждение Этапа 1 о тарифах Astralio `250 / 650 / 1990 ⭐` было неточным: фактическая проверка кода `astralio/services/premium_service.py:16-57` показала тарифы **`199 ⭐` (30 дн.) / `499 ⭐` (90 дн.) / `1499 ⭐` (365 дн.)**.
> 3. Утверждение о доле «60–70% первых оплат через микроплатежи» является неподтверждённой гипотезой и исключено из доказанных выводов в Разделе III.

---

# РАЗДЕЛ III. ЭТАП 2 — ПРОВЕРКА ДОСТОВЕРНОСТИ ИССЛЕДОВАНИЯ КОНКУРЕНТОВ

> **Инструментальные границы проверки:**
> - Из серверного контейнера без личного MTProto-аккаунта невозможно отправить `/start` в чужой бот (Bot API запрещает ботам писать другим ботам). Поэтому **ручная проверка интерфейса внутри Telegram-клиента не выполнялась ни для одного из 29 ботов**.
> - HTTP-ответ `https://t.me/<username>` используется **только** для подтверждения существования юзернейма, `Title` и `Bio`, но **не** приравнивается к доказательству живой работы сервера бота.

## 1. Классификация всех 29 ботов по степени достоверности (A / B / C / D)

| № | Username | Прямая ссылка `t.me` | Бот существует? | Публичные доказательства функционала | Интерфейс проверен вручную в TG? | Доступны ли цены публично? | Подтверждённая аудитория (MAU) | Категория |
|---|---|---|---|---|---|---|---|---|
| 1 | `@SuperTarologBot` | [t.me/SuperTarologBot](https://t.me/SuperTarologBot) | Да | Да: [superastro.ru](https://superastro.ru), [оферта](https://superastro.ru/oferta), [правила оплаты](https://superastro.ru/oplata-i-vozvrat), Mini App `app.superastro.ru` | Нет | Частично (модель Stars + ЮKassa + кристаллы; цифры внутри бота) | Нет данных MAU (канал `@superastro_ru`: 341 подп.) | **A** |
| 2 | `@tarotnatalbot` | [t.me/tarotnatalbot](https://t.me/tarotnatalbot) | Да | Да: [оферта Teletype](https://teletype.in/@tarotnatalbot/legaldoc), [Grambots](https://www.grambots.com/ru/bots/tarotnatalbot), [MiniTelegram](https://minitelegram.com/ru/apps/tarotnatalbot) | Нет | Частично (Stars + ЮKassa, 3 бесплатных кредита; прайс внутри бота) | Да: **744,3 тыс.** (`20.11.2026`, MiniTelegram) / 1 079 275 (Grambots) | **A** |
| 3 | `@arcanagurubot` | [t.me/arcanagurubot](https://t.me/arcanagurubot) | Да | Да: [arcana.guru](https://arcana.guru), [Grambots](https://www.grambots.com/ru/bots/arcanagurubot), [MiniTelegram](https://minitelegram.com/ru/apps/arcanagurubot) | Нет | Нет (внутри Mini App) | Да: **24,7 тыс.** (`20.11.2026`, -84%) / 161 363 (Grambots `01.09.2026`) | **A** |
| 4 | `@astrotaybot` | [t.me/astrotaybot](https://t.me/astrotaybot) | Да | Да: [astrotay.ru](https://astrotay.ru) | Нет | Нет («Бесплатный старт», тарифы внутри бота) | Нет данных MAU | **A** |
| 5 | `@fate_whisper_bot` | [t.me/fate_whisper_bot](https://t.me/fate_whisper_bot) | Да | Да: [fate-whisper.ru](https://fate-whisper.ru), [Условия](https://fate-whisper.ru/terms), [Политика ПД](https://fate-whisper.ru/privacy) | Нет | Частично (только Telegram Stars; бесплатные лимиты описаны) | Нет данных MAU (канал `@fate_whisper_tarot`: 67 подп.) | **A** |
| 6 | `@celestifyBot` | [t.me/celestifyBot](https://t.me/celestifyBot) | Да | Да: [celestify.me](https://celestify.me), [MiniTelegram](https://minitelegram.com/ru/apps/celestifybot) | Нет | **Да (точные цены):** 59 ⭐ за 1 PDF, 179 ⭐ за 4 PDF | Да: **184 MAU** (`22.09.2026`, MiniTelegram) | **A** |
| 7 | `@taro_gpt_bot` | [t.me/taro_gpt_bot](https://t.me/taro_gpt_bot) | Да | Да: [tarogpt.ru](https://tarogpt.ru), [Оферта](https://tarogpt.ru/legal/tarobot-terms), [MiniTelegram](https://minitelegram.com/ru/apps/taro_gpt_bot), [Grambots](https://www.grambots.com/ru/bots/taro_gpt_bot) | Нет | Частично (ЮMoney `/premium`, реферальные промокоды; цифры в боте) | Да: **29,4 тыс.** (`20.11.2026`, +5,8%) / 33 196 (Grambots) | **A** |
| 8 | `@tarolog10_bot` | [t.me/tarolog10_bot](https://t.me/tarolog10_bot) | Да | Да: [Grambots](https://www.grambots.com/ru/bots/tarolog10_bot), [MiniTelegram](https://minitelegram.com/ru/apps/tarolog10_bot) | Нет | Нет | Да: **46,4 тыс.** (`20.11.2026`, +44,5%) / 247 886 (Grambots `04.07.2026`) | **A** |
| 9 | `@apluna_bot` | [t.me/apluna_bot](https://t.me/apluna_bot) | Да | Да: [MiniTelegram](https://minitelegram.com/ru/apps/apluna_bot) | Нет | Частично («первый разбор бесплатный») | Да: **50,4 тыс.** (`09.11.2026`, MiniTelegram) | **A** |
| 10 | `@oracul_tarot_bot` | [t.me/oracul_tarot_bot](https://t.me/oracul_tarot_bot) | Да | Да: [MiniTelegram](https://minitelegram.com/ru/apps/oracul_tarot_bot) | Нет | Частично (`first readings are free`) | Да: **1,5 тыс.** (`20.11.2026`, +38,5%) | **A** |
| 11 | `@mystic_companion_bot` | [t.me/mystic_companion_bot](https://t.me/mystic_companion_bot) | Да | Да: [MiniTelegram](https://minitelegram.com/ru/apps/mystic-companion-tarot) | Нет | Нет | Нет данных MAU | **A** |
| 12 | `@smartytoolsbot` | [t.me/smartytoolsbot](https://t.me/smartytoolsbot) | Да | Да: каталог `tlg.me` | Нет | Частично (PDF за Telegram Stars, без точной суммы) | Нет данных MAU | **A** |
| 13 | `@gadalka_topbot` | [t.me/gadalka_topbot](https://t.me/gadalka_topbot) | Да | Да: [MiniTelegram](https://minitelegram.com/ru/apps/gadalka_topbot) | Нет | Нет | Да: **26,4 тыс.** (`21.11.2026`, +8,5%) | **A** |
| 14 | `@horoscopesoflovebot` | [t.me/horoscopesoflovebot](https://t.me/horoscopesoflovebot) | Да | Да: [MiniTelegram](https://minitelegram.com/ru/apps/horoscopesoflovebot) | Нет | Нет | Да: **19,6 тыс.** (`21.11.2026`, -10,2%) | **A** |
| 15 | `@taroluxebot` | [t.me/taroluxebot](https://t.me/taroluxebot) | Да | Да: [MiniTelegram](https://minitelegram.com/ru/apps/taroluxebot) | Нет | Частично (бесплатный стартовый расклад) | Да: **4,5 тыс.** (`21.11.2026`, -3,3%) | **A** |
| 16 | `@starsvoice_bot` | [t.me/starsvoice_bot](https://t.me/starsvoice_bot) | Да | Да: [MiniTelegram](https://minitelegram.com/ru/apps/starsvoice_bot) | Нет | Нет | Да: **2,4 тыс.** (`20.11.2026`, +1,7%) | **A** |
| 17 | `@taroshenka_bot` | [t.me/taroshenka_bot](https://t.me/taroshenka_bot) | Да | Да: [MiniTelegram](https://minitelegram.com/ru/apps/taroshenka_bot) | Нет | Частично (бесплатный лунный календарь) | Да: **555–586** (`21.11.2026`) | **A** |
| 18 | `@quantomant_bot` | [t.me/quantomant_bot](https://t.me/quantomant_bot) | Да | Да: [MiniTelegram](https://minitelegram.com/ru/apps/quantomant_bot) | Нет | Да (механика): карта дня бесплатно 1 раз/сут, кристаллы на 3 расклада в подарок | Да: **541** (`20.11.2026`, +117,3%) | **A** |
| 19 | `@NatalChartRobot` | [t.me/NatalChartRobot](https://t.me/NatalChartRobot) | Да | Да: [MiniTelegram](https://minitelegram.com/ru/apps/NatalChartRobot) | Нет | Нет | Да: **54** (`28.09.2026`, 0%) | **A** |
| 20 | `@OracleAstro_Bot` | [t.me/OracleAstro_Bot](https://t.me/OracleAstro_Bot) | Да | Да: [MiniTelegram](https://minitelegram.com/ru/apps/OracleAstro_Bot) | Нет | Нет | Да: **27** (`20.09.2026`, 0%) | **A** |
| 21 | `@esotero_bot` | [t.me/esotero_bot](https://t.me/esotero_bot) | Да | Нет (только Bio `t.me`) | Нет | Нет | Нет данных | **B** |
| 22 | `@LunairaBot` | [t.me/LunairaBot](https://t.me/LunairaBot) | Да | Слабые (Bio `t.me`, упоминания YouTube) | Нет | Нет | Нет данных | **B** |
| 23 | `@Natalchart1_bot` | [t.me/Natalchart1_bot](https://t.me/Natalchart1_bot) | Да | Нет (только Bio `t.me`) | Нет | Нет | Нет данных | **B** |
| 24 | `@tarolog_astro_bot` | [t.me/tarolog_astro_bot](https://t.me/tarolog_astro_bot) | Да | Нет (только Bio `t.me`) | Нет | Нет | Нет данных | **B** |
| 25 | `@smart_zodiac_bot` | [t.me/smart_zodiac_bot](https://t.me/smart_zodiac_bot) | Да | Нет (только Bio `t.me`) | Нет | Нет | Нет данных | **B** |
| 26 | `@astromoon_ai_bot` | [t.me/astromoon_ai_bot](https://t.me/astromoon_ai_bot) | Да | Нет (только Bio `t.me`) | Нет | Нет | Нет данных | **B** |
| 27 | `@mystaramagicbot` | [t.me/mystaramagicbot](https://t.me/mystaramagicbot) | Да | Нет (только Bio `t.me`) | Нет | Нет | Нет данных | **B** |
| 28 | `@nocturnabot_rubot` | [t.me/nocturnabot_rubot](https://t.me/nocturnabot_rubot) | Да | Слабые (Bio `t.me` + короткий анонс) | Нет | Частично (глубокие расклады за Stars, без цифр) | Нет данных | **B** |
| 29 | `@milanatarba_newbot` / `@astroluminary_bot` | [t.me/milanatarba_newbot](https://t.me/milanatarba_newbot) / [t.me/astroluminary_bot](https://t.me/astroluminary_bot) | Да (оба) | Неполные: у `@milanatarba_newbot` пустое Bio в `t.me`; у `AstroLuminary` битая ссылка в MiniTelegram | Нет | `AstroLuminary`: **7 дней за 1 ₽** (MiniTelegram) | `@milanatarba_newbot`: **16 тыс.** (`19.11.2026`); `@astroluminary_bot`: Н/Д | **C** |

* **Категория D (не удалось подтвердить существование):** 0 из списка 29 ботов (пробные угаданные варианты `@luminary_astro_bot`, `@astroluminarybot` не существуют).

---

## 2. Проверка аудитории (MAU)

* **Источник 1:** `minitelegram.com` (независимый трекер поля Telegram API `bot_active_users` с датой последнего опроса `19–21.11.2026` и окном сравнения `21 окт. 2026 — 20 нояб. 2026 UTC`).
* **Источник 2:** `grambots.com` (независимый каталог со статичным снимком MAU на дату индексации карточки без графика по дням).
* **Ключевые подтверждённые цифры MAU:**
  * `@tarotnatalbot`: **744,3 тыс. MAU** (+30%, `20.11.2026`, [MiniTelegram](https://minitelegram.com/ru/apps/tarotnatalbot)) / **1 079 275 MAU** (ранний пиковый снимок, [Grambots](https://www.grambots.com/ru/bots/tarotnatalbot)).
  * `@apluna_bot`: **50,4 тыс. MAU** (`09.11.2026`, [MiniTelegram](https://minitelegram.com/ru/apps/apluna_bot)).
  * `@tarolog10_bot`: **46,4 тыс. MAU** (+44,5%, `20.11.2026`, [MiniTelegram](https://minitelegram.com/ru/apps/tarolog10_bot)) / **247 886 MAU** (снимок от `04.07.2026`, [Grambots](https://www.grambots.com/ru/bots/tarolog10_bot)).
  * `@taro_gpt_bot`: **29,4 тыс. MAU** (+5,8%, `20.11.2026`, [MiniTelegram](https://minitelegram.com/ru/apps/taro_gpt_bot)) / **33 196 MAU** (`04.07.2026`, [Grambots](https://www.grambots.com/ru/bots/taro_gpt_bot)).
  * `@gadalka_topbot`: **26,4 тыс. MAU** (+8,5%, `21.11.2026`, [MiniTelegram](https://minitelegram.com/ru/apps/gadalka_topbot)).
  * `@arcanagurubot`: **24,7 тыс. MAU** (-84%, `20.11.2026`, [MiniTelegram](https://minitelegram.com/ru/apps/arcanagurubot)) / **161 363 MAU** (`01.09.2026`, [Grambots](https://www.grambots.com/ru/bots/arcanagurubot)) — оба источника сходятся математически (`161 363 × 0.16 ≈ 25.8K`).
  * `@horoscopesoflovebot`: **19,6 тыс. MAU** (-10,2%, `21.11.2026`, [MiniTelegram](https://minitelegram.com/ru/apps/horoscopesoflovebot)).
  * `@milanatarba_newbot`: **16,0 тыс. MAU** (+27,9%, `19.11.2026`, [MiniTelegram](https://minitelegram.com/ru/apps/milanatarba_newbot)).
  * `@taroluxebot`: **4,5 тыс. MAU** (`21.11.2026`), `@starsvoice_bot`: **2,4 тыс. MAU** (`20.11.2026`), `@oracul_tarot_bot`: **1,5 тыс. MAU** (+38,5%, `20.11.2026`), `@taroshenka_bot`: **555–586 MAU** (`21.11.2026`), `@quantomant_bot`: **541 MAU** (+117,3%, `20.11.2026`), `@celestifyBot`: **184 MAU** (`22.09.2026`), `@NatalChartRobot`: **54 MAU** (`28.09.2026`), `@OracleAstro_Bot`: **27 MAU** (`20.09.2026`).
  * Подписчики каналов (`@superastro_ru` — 341, `@fate_whisper_tarot` — 67) **не считаются** активной аудиторией ботов.

---

## 3. Документально подтверждённые цены и монетизация

| Бот | Telegram Stars (⭐) | Рубли / Эквайринг | Внутренняя валюта и Free-лимиты | Реферальная система | Источник |
|---|---|---|---|---|---|
| `@celestifyBot` | **59 ⭐** за 1 PDF-разбор (`/natal`, `/numerology`, `/horoscope`, `/astrocartography`); **179 ⭐** за пакет из 4 PDF | Нет | Разовые покупки без подписки | Не заявлена | [celestify.me](https://celestify.me) |
| `@astroluminary_bot` | Нет публичных цифр | **Пробный доступ 7 дней за 1 ₽** | Первый прогноз бесплатно | Не заявлена | [MiniTelegram](https://minitelegram.com/ru/apps/astroluminary), [t.me/astroluminary_bot](https://t.me/astroluminary_bot) |
| `@SuperTarologBot` | Приём Stars подтверждён (цены внутри бота) | **ЮKassa** (Visa/MC/МИР, цены внутри бота) | **«Кристаллы»**: ежедневное бесплатное начисление; бесплатно Карта дня, гороскоп, базовый натал | Не заявлена | [superastro.ru](https://superastro.ru), [оферта](https://superastro.ru/oferta), [оплата](https://superastro.ru/oplata-i-vozvrat) |
| `@tarotnatalbot` | Приём Stars подтверждён (цены внутри бота) | **ЮKassa** (ИП Карамов А.Ф.) | **«Кредиты» + Premium**: на старте **3 бесплатных кредита + Карта дня** + «Колесо фортуны» | Не заявлена в оферте | [Оферта Teletype](https://teletype.in/@tarotnatalbot/legaldoc), [Grambots](https://www.grambots.com/ru/bots/tarotnatalbot) |
| `@fate_whisper_bot` | **Только Telegram Stars** (подписки, отдельные расклады, наборы; цифры в боте) | Нет | Бесплатно: Карта дня (раз/24 ч), гороскопы, Звёздный паспорт, Коллекция 78 карт, квесты, **стрик 7 дней** | **Да** (реферальный код в Политике ПД + партнёрка) | [fate-whisper.ru](https://fate-whisper.ru), [terms](https://fate-whisper.ru/terms), [privacy](https://fate-whisper.ru/privacy) |
| `@taro_gpt_bot` | Не упомянуты | **ЮMoney** (`/premium`, пакеты и безлимит) | Есть бесплатный лимит запросов | **Да** (промокоды за приглашение друзей, п. 5.9 оферты) | [Оферта tarogpt.ru](https://tarogpt.ru/legal/tarobot-terms) |
| `@quantomant_bot` | Нет публичных цифр | Нет публичных цифр | **«Кристаллы»**: Карта дня 1 раз/сут бесплатно + **кристаллы на 3 первых расклада** | Нет данных | [MiniTelegram](https://minitelegram.com/ru/apps/quantomant_bot) |
| `@smartytoolsbot` | Оплата PDF за Stars подтверждена (без цифр) | Нет данных | Короткие ответы в чате бесплатно | Нет данных | Каталог `tlg.me` |
| `@nocturnabot_rubot` | Глубокие расклады за Stars (без цифр) | Нет данных | Базовая часть бесплатно | Нет данных | [t.me/nocturnabot_rubot](https://t.me/nocturnabot_rubot) |

---

## 4. Исправление 5 ключевых утверждений Этапа 1

1. **`@tarotnatalbot` — лидер по MAU:** **Подтверждено с оговоркой** — №1 среди всех 72 проиндексированных ботов категории в `minitelegram.com` (744,3 тыс. MAU на 20.11.2026), но без учёта неиндексированных ботов (`@SuperTarologBot`, `@astrotaybot`) и только в сегменте AI-Таро (реальной натальной карты в нём нет).
2. **Дополнительные вопросы/карты дают 60–70% выручки:** **Не подтверждено в части процента** — факт продажи доп. вопросов и карт подтверждён офертой `@tarotnatalbot` (п. 6), но финансовые доли выручки не публичны и исключены как гипотеза.
3. **PDF-отчёты за Stars востребованы:** **Подтверждено как модель у 4 ботов (`@celestifyBot`, `@smartytoolsbot`, `@mystic_companion_bot`, `@NatalChartRobot`)**, но у узких PDF-ботов малый MAU (`184` и `54`), поэтому PDF — это дополнительный оффер, а не замена интерактивному диалогу.
4. **Синтез натальной карты и Таро — свободная ниша:** **Опровергнуто** — уже реализован у `@mystic_companion_bot` и `@quantomant_bot`, хотя у них пока небольшой трафик, а у гигантов AI-Таро (`@tarotnatalbot`, `@arcanagurubot`) реальной астрономической карты нет.
5. **Astralio технически превосходит большинство конкурентов:** **Скорректировано** — превосходит простые Таро-боты за счёт реальных эфемерид `pyswisseph`, но `@SuperTarologBot`, `@astroluminary_bot` и `@celestifyBot` также используют реальные эфемериды и превосходят текущий MVP Astralio по Mini App-визуализации, диалоговым уточнениям и активному биллингу.

---

## 5. Итоговый ТОП-5 наиболее опасных конкурентов и 5 приоритетных функций для Astralio

### ТОП-5 опасных Telegram-конкурентов (только из Категории A)
1. **`@SuperTarologBot` (`Super Astro`)** — сильнейший функциональный конкурент (натал с домами + транзитный прогноз дня + синастрия + 78 Таро / 36 Ленорман + Матрица + AI-чат + ежедневные кристаллы + Stars/ЮKassa).
2. **`@tarotnatalbot`** — сильнейший трафиковый конкурент (744,3 тыс. MAU, +30%, диалоговые уточнения и доп. карта, 3 кредита на старте, Колесо фортуны, Stars/ЮKassa).
3. **`@apluna_bot` (`LUNA`)** — крупнейший подтверждённый астро-комбайн (50,4 тыс. MAU, натал, прогноз по карте, Таро, хиромантия, разбор переписки).
4. **`@mystic_companion_bot`** — ближайший концептуальный конкурент (Карта дня по наталу и фазе Луны, синастрия по кросс-аспектам, PDF натала, AI-Мастер).
5. **`@fate_whisper_bot`** — эталон удержания и 100% Stars-монетизации (Коллекция 78 карт, стрик 7 дней, квесты, реферальная система).

### 5 наиболее перспективных функций для Astralio
1. **Диалоговое продолжение (Follow-up Q&A + доп. карта)** прямо под раскладом Таро, натальной картой и синастрией.
2. **Ежедневная «Астро-Карта дня»** (синтез `TarotService` + реального транзита `pyswisseph` к наталу пользователя).
3. **Welcome-бонус (3 премиум-разбора) + Коллекция 78 Арканов и Стрик 7 дней** поверх существующей истории в `ReadingRepository`.
4. **PDF-отчёты натальной карты и синастрии в чат за 59–179 ⭐** (низкий порог первой оплаты).
5. **Виральные модули:** кнопка `💌 Проверить совместимость со мной` (deep-link), сохранение профилей партнёров + прогноз для пары, релокация/астрокартография.
