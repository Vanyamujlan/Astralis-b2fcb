import {
  Compass,
  Heart,
  HelpCircle,
  Layers,
  ShieldCheck,
  Sparkles,
  Star,
  Sun,
  Terminal,
  User,
} from 'lucide-react';
import {useState} from 'react';

interface BotScreen {
  id: string;
  label: string;
  icon: typeof Sparkles;
  title: string;
  summary: string;
  sampleOutput: string[];
  buttons: string[];
}

const BOT_SCREENS: BotScreen[] = [
  {
    id: 'natal',
    label: 'Натальная карта',
    icon: Sparkles,
    title: 'Натальная карта — Swiss Ephemeris',
    summary:
      'Пошаговый ввод даты, времени и места рождения с реальным расчётом 10 планет, Асцендента, Середины Неба, 12 домов и аспектов.',
    sampleOutput: [
      '☉ Солнце: ♉ Телец 24°10′ · 9 дом',
      '☽ Луна: ♐ Стрелец 06°42′ · 3 дом',
      '⬆️ Асцендент (I дом): ♍ Дева 25°14′',
      '⚠️ При неизвестном времени дома не выдумываются — явно выводятся ограничения расчёта.',
    ],
    buttons: ['Рассчитать по моему профилю', 'Ввести данные рождения', 'Главное меню'],
  },
  {
    id: 'compat',
    label: 'Совместимость',
    icon: Heart,
    title: 'Синастрия двух карт',
    summary:
      'Сравнение сохранённого профиля с партнёром или ввод двух человек шаг за шагом с расчётом реальных межкартовых аспектов.',
    sampleOutput: [
      '🌟 Общая совместимость рассчитывается по синастрическим аспектам и стихиям',
      '• Эмоциональная связь · Романтика и притяжение',
      '• Общение и взаимопонимание · Долгосрочный потенциал',
      '✦ Сильные стороны, зоны внимания и понятная рекомендация',
    ],
    buttons: ['Мой профиль + партнёр', 'Ввести данные двух людей', 'Главное меню'],
  },
  {
    id: 'forecast',
    label: 'Прогнозы',
    icon: Sun,
    title: 'Персональные транзитные прогнозы',
    summary:
      'Ежедневный (1 день) и недельный (7 дней) расчёт реальных текущих транзитов планет к натальной карте пользователя.',
    sampleOutput: [
      '🌅 Прогноз на сегодня и 🗓 Прогноз на неделю',
      '• Активные транзиты: орбы, гармоничные (✦) и напряжённые (⚡) аспекты',
      '• Без даты рождения бот просит заполнить профиль, не подменяя расчёт случайным текстом',
    ],
    buttons: ['Прогноз на сегодня', 'Прогноз на неделю', 'Главное меню'],
  },
  {
    id: 'tarot',
    label: 'Таро',
    icon: Layers,
    title: 'Колода Таро (78 карт) + история',
    summary:
      'Полная колода Райдера–Уэйта на русском: 4 расклада, криптографическая выборка без повторов, прямое/перевёрнутое положение и Firestore-история.',
    sampleOutput: [
      '🎴 Карта дня (1) · ⏳ Прошлое/Настоящее/Будущее (3)',
      '💞 Отношения (3) · 🧭 Выбор пути (5)',
      '🔄 Отдельные значения для прямых и перевёрнутых карт',
      '📚 Каждый расклад сохраняется в users/{id}/tarot_readings',
    ],
    buttons: ['Карта дня (1 карта)', 'Выбор пути (5 карт)', 'История раскладов'],
  },
  {
    id: 'profile',
    label: 'Профиль',
    icon: User,
    title: 'Профиль и данные рождения',
    summary:
      'Автоматическая регистрация Telegram-пользователя и безопасное merge-обновление даты, времени и места рождения в Firestore.',
    sampleOutput: [
      '• Telegram ID, имя, username синхронизируются автоматически',
      '• Встроенный офлайн-справочник 85+ городов + ввод координат + Nominatim',
      '• Автоопределение часового пояса через timezonefinder',
    ],
    buttons: ['Изменить дату рождения', 'Изменить время рождения', 'Изменить место рождения'],
  },
  {
    id: 'premium',
    label: 'Premium',
    icon: Star,
    title: 'Тарифы и архитектура Telegram Stars',
    summary:
      'Проверка реального статуса подписки, тарифы в Stars (XTR), PreCheckoutQueryHandler и идемпотентный реестр платежей.',
    sampleOutput: [
      '⭐ 1 месяц (199 Stars) · 3 месяца (499 Stars) · 1 год (1499 Stars)',
      '🔒 Защита от дублей платежей по charge_id в коллекции payments/',
      '• Никакой имитации оплаты: активация только по подтверждённому платежу Telegram',
    ],
    buttons: ['1 месяц — 199 Stars', 'Проверить статус подписки', 'Главное меню'],
  },
  {
    id: 'help',
    label: 'Помощь',
    icon: HelpCircle,
    title: 'Инструкции и обратная связь',
    summary:
      'Подробный справочник по всем разделам, сохранение обратной связи в Firestore и защита от неизвестных команд и битых callback_data.',
    sampleOutput: [
      '📖 Инструкция по всем 7 разделам Astralio',
      '✉️ Пошаговая форма обратной связи -> feedback/{id}',
      '🛡️ Корректная обработка /unknown, устаревших и некорректных callback_data',
    ],
    buttons: ['Инструкция по функциям', 'Оставить обратную связь', 'Главное меню'],
  },
];

const ENV_VARS = [
  {name: 'BOT_TOKEN', required: true, note: 'Токен бота от @BotFather'},
  {name: 'FIREBASE_PROJECT_ID', required: true, note: 'ID проекта Firebase / GCP'},
  {name: 'FIREBASE_CLIENT_EMAIL', required: true, note: 'Email сервисного аккаунта'},
  {name: 'FIREBASE_PRIVATE_KEY', required: true, note: 'Приватный ключ сервисного аккаунта'},
  {name: 'FIREBASE_DATABASE_ID', required: false, note: 'Опциональное имя базы Firestore'},
  {name: 'AI_API_KEY', required: false, note: 'Опционально — без ключа работает локальный движок'},
  {name: 'TELEGRAM_STARS_ENABLED', required: false, note: 'false по умолчанию до активации Stars'},
];

export default function App() {
  const [activeId, setActiveId] = useState<string>('natal');
  const activeScreen = BOT_SCREENS.find((s) => s.id === activeId) ?? BOT_SCREENS[0];
  const ActiveIcon = activeScreen.icon;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 antialiased selection:bg-indigo-500/30">
      <div className="mx-auto max-w-5xl px-6 py-10">
        <header className="border-b border-slate-800/80 pb-8">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500/15 text-indigo-300 ring-1 ring-indigo-400/25">
              <Compass className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-2xl font-semibold tracking-tight text-white">Astralio</h1>
              <p className="text-sm text-slate-400">
                Python 3.12+ Telegram Bot MVP · python-telegram-bot 22.x · Swiss Ephemeris · Firestore
              </p>
            </div>
          </div>
          <p className="mt-4 max-w-3xl text-sm leading-relaxed text-slate-300">
            Исходный код Telegram-бота развёрнут в пакете <code className="rounded bg-slate-900 px-1.5 py-0.5 text-indigo-300">astralio/</code> с модульной
            архитектурой, полным покрытием тестами и GitHub Actions CI. Ниже представлен интерактивный обзор
            всех 7 разделов интерфейса бота и требуемых переменных окружения для запуска воркера.
          </p>
        </header>

        <main className="mt-8 grid gap-8 lg:grid-cols-12">
          <section className="lg:col-span-5">
            <h2 className="text-xs font-medium tracking-wider text-slate-400 uppercase">
              Главное меню Astralio (7 модулей)
            </h2>
            <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-1">
              {BOT_SCREENS.map((screen) => {
                const Icon = screen.icon;
                const isSelected = screen.id === activeId;
                return (
                  <button
                    key={screen.id}
                    type="button"
                    onClick={() => setActiveId(screen.id)}
                    className={`flex items-center gap-3 rounded-xl border px-4 py-3 text-left transition ${
                      isSelected
                        ? 'border-indigo-400/50 bg-indigo-500/15 text-white'
                        : 'border-slate-800 bg-slate-900/60 text-slate-300 hover:border-slate-700 hover:bg-slate-900'
                    }`}
                  >
                    <Icon className={`h-4 w-4 shrink-0 ${isSelected ? 'text-indigo-300' : 'text-slate-400'}`} />
                    <span className="text-sm font-medium">{screen.label}</span>
                  </button>
                );
              })}
            </div>
          </section>

          <section className="lg:col-span-7">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
              <div className="flex items-center gap-2.5 text-indigo-300">
                <ActiveIcon className="h-5 w-5" />
                <h2 className="text-lg font-semibold text-white">{activeScreen.title}</h2>
              </div>
              <p className="mt-2 text-sm leading-relaxed text-slate-300">{activeScreen.summary}</p>

              <div className="mt-5 rounded-xl border border-slate-800 bg-slate-950/80 p-4 font-mono text-xs leading-6 text-slate-200">
                {activeScreen.sampleOutput.map((line) => (
                  <div key={line}>{line}</div>
                ))}
              </div>

              <div className="mt-4 flex flex-wrap gap-2">
                {activeScreen.buttons.map((btn) => (
                  <span
                    key={btn}
                    className="rounded-lg border border-slate-700/80 bg-slate-800/70 px-3 py-1.5 text-xs text-slate-200"
                  >
                    {btn}
                  </span>
                ))}
              </div>
            </div>

            <div className="mt-6 rounded-2xl border border-slate-800 bg-slate-900/50 p-6">
              <div className="flex items-center gap-2 text-slate-200">
                <ShieldCheck className="h-4 w-4 text-emerald-400" />
                <h3 className="text-sm font-semibold">Переменные окружения (.env / Railway)</h3>
              </div>
              <div className="mt-3 divide-y divide-slate-800/80 text-xs">
                {ENV_VARS.map((item) => (
                  <div key={item.name} className="flex flex-col gap-1 py-2 sm:flex-row sm:items-center sm:justify-between">
                    <div className="flex items-center gap-2">
                      <code className="font-mono text-indigo-300">{item.name}</code>
                      <span className="text-[11px] text-slate-400">
                        {item.required ? '(обязательно)' : '(опционально)'}
                      </span>
                    </div>
                    <span className="text-slate-400">{item.note}</span>
                  </div>
                ))}
              </div>

              <div className="mt-4 flex items-center gap-2 rounded-lg bg-slate-950 px-3 py-2 font-mono text-xs text-slate-300">
                <Terminal className="h-3.5 w-3.5 text-indigo-400" />
                <span>python -m astralio.main</span>
              </div>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}
