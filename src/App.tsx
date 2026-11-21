import {type User as FirebaseUser, onAuthStateChanged} from 'firebase/auth';
import {
  collection,
  deleteDoc,
  doc,
  getDoc,
  limit,
  onSnapshot,
  orderBy,
  query,
  serverTimestamp,
  setDoc,
  updateDoc,
  where,
} from 'firebase/firestore';
import {
  Compass,
  Heart,
  HelpCircle,
  Layers,
  LogIn,
  LogOut,
  Save,
  Send,
  ShieldCheck,
  Sparkles,
  Star,
  Sun,
  Terminal,
  Trash2,
  User,
} from 'lucide-react';
import {type FormEvent, useEffect, useState} from 'react';
import {
  OperationType,
  auth,
  db,
  firebaseProjectMeta,
  handleFirestoreError,
  signInWithGoogle,
  signOutUser,
} from './firebase.ts';

interface BotScreen {
  id: string;
  label: string;
  icon: typeof Sparkles;
  title: string;
  summary: string;
  sampleOutput: string[];
  buttons: string[];
}

interface StoredProfile {
  uid: string;
  displayName: string;
  birthDate: string;
  birthTime: string;
  birthTimeUnknown: boolean;
  birthPlace: string;
}

interface StoredTarotReading {
  readingId: string;
  uid: string;
  spreadType: 'one_card' | 'three_cards' | 'relationship' | 'path_choice';
  spreadTitle: string;
  question: string;
  cardsSummary: string;
  summary: string;
}

interface StoredFeedback {
  feedbackId: string;
  uid: string;
  message: string;
  status: 'open' | 'reviewed';
}

const BIRTH_DATE_RE = /^(|\d{4}-\d{2}-\d{2})$/;
const BIRTH_TIME_RE = /^(|\d{2}:\d{2})$/;

const QUICK_TAROT_CARDS = [
  {name: '0. Шут', upright: 'Новое начало и свобода выбора.', reversed: 'Проверьте детали перед риском.'},
  {name: 'I. Маг', upright: 'Все ресурсы для результата уже у вас.', reversed: 'Соберите фокус в одну задачу.'},
  {name: 'II. Верховная Жрица', upright: 'Доверяйте интуиции и наблюдайте.', reversed: 'Часть фактов ещё не раскрыта.'},
  {name: 'III. Императрица', upright: 'Период роста, заботы и созидания.', reversed: 'Восстановите личный ресурс.'},
  {name: 'VI. Влюблённые', upright: 'Выбор сердца и искреннее согласие.', reversed: 'Определите честные приоритеты.'},
  {name: 'X. Колесо Фортуны', upright: 'Поворот цикла и удачный шанс.', reversed: 'Адаптируйтесь к новому ритму.'},
  {name: 'XVII. Звезда', upright: 'Вдохновение, надежда и ясность пути.', reversed: 'Сохраняйте веру в долгую цель.'},
  {name: 'XIX. Солнце', upright: 'Радость, открытость и заслуженный успех.', reversed: 'Не обесценивайте сделанные шаги.'},
  {name: 'XXI. Мир', upright: 'Гармоничное завершение важного этапа.', reversed: 'Доведите финальный штрих до конца.'},
];

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
      '📚 Каждый расклад сохраняется в Firestore',
    ],
    buttons: ['Карта дня (1 карта)', 'Выбор пути (5 карт)', 'История раскладов'],
  },
  {
    id: 'profile',
    label: 'Профиль',
    icon: User,
    title: 'Профиль и данные рождения',
    summary:
      'Автоматическая регистрация и безопасное сохранение даты, времени и места рождения в Google Cloud Firestore.',
    sampleOutput: [
      '• Профиль изолирован по владельцу (owner-only rules)',
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

function createDocId(prefix: string): string {
  const rand = crypto.getRandomValues(new Uint32Array(2));
  return `${prefix}_${Date.now().toString(36)}_${rand[0].toString(36)}${rand[1].toString(36)}`.slice(
    0,
    60,
  );
}

export default function App() {
  const [activeId, setActiveId] = useState<string>('natal');
  const [authReady, setAuthReady] = useState(false);
  const [user, setUser] = useState<FirebaseUser | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);

  // Live Firestore Profile state
  const [profileExists, setProfileExists] = useState(false);
  const [displayName, setDisplayName] = useState('');
  const [birthDate, setBirthDate] = useState('');
  const [birthTime, setBirthTime] = useState('');
  const [birthTimeUnknown, setBirthTimeUnknown] = useState(false);
  const [birthPlace, setBirthPlace] = useState('');
  const [profileNotice, setProfileNotice] = useState<string | null>(null);
  const [savingProfile, setSavingProfile] = useState(false);

  // Live Firestore Tarot Readings
  const [readings, setReadings] = useState<StoredTarotReading[]>([]);
  const [tarotQuestion, setTarotQuestion] = useState('');
  const [drawingTarot, setDrawingTarot] = useState(false);

  // Live Firestore Feedback
  const [feedbackList, setFeedbackList] = useState<StoredFeedback[]>([]);
  const [feedbackText, setFeedbackText] = useState('');
  const [feedbackNotice, setFeedbackNotice] = useState<string | null>(null);
  const [sendingFeedback, setSendingFeedback] = useState(false);

  const activeScreen = BOT_SCREENS.find((s) => s.id === activeId) ?? BOT_SCREENS[0];
  const ActiveIcon = activeScreen.icon;

  // 1. Track Firebase Auth state
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (nextUser) => {
      setUser(nextUser);
      setAuthReady(true);
      if (!nextUser) {
        setProfileExists(false);
        setReadings([]);
        setFeedbackList([]);
      }
    });
    return () => unsubscribe();
  }, []);

  // 2. Load user profile & attach authenticated Firestore listeners ONLY when signed in
  useEffect(() => {
    if (!authReady || !user) {
      return;
    }

    const userPath = `users/${user.uid}`;
    let cancelled = false;

    const loadProfile = async () => {
      try {
        const snap = await getDoc(doc(db, 'users', user.uid));
        if (cancelled) {
          return;
        }
        if (snap.exists()) {
          const data = snap.data() as Partial<StoredProfile>;
          setProfileExists(true);
          setDisplayName(data.displayName || user.displayName || 'Пользователь');
          setBirthDate(data.birthDate || '');
          setBirthTime(data.birthTime || '');
          setBirthTimeUnknown(Boolean(data.birthTimeUnknown));
          setBirthPlace(data.birthPlace || '');
        } else {
          setProfileExists(false);
          setDisplayName((user.displayName || 'Пользователь').slice(0, 100));
          setBirthDate('');
          setBirthTime('');
          setBirthTimeUnknown(false);
          setBirthPlace('');
        }
      } catch (error) {
        handleFirestoreError(error, OperationType.GET, userPath);
      }
    };

    void loadProfile();

    const tarotPath = `users/${user.uid}/tarotReadings`;
    const tarotQuery = query(
      collection(db, 'users', user.uid, 'tarotReadings'),
      where('uid', '==', user.uid),
      orderBy('createdAt', 'desc'),
      limit(10),
    );
    const unsubTarot = onSnapshot(
      tarotQuery,
      (snapshot) => {
        setReadings(snapshot.docs.map((d) => d.data() as StoredTarotReading));
      },
      (error) => {
        handleFirestoreError(error, OperationType.LIST, tarotPath);
      },
    );

    const feedbackPath = 'feedback';
    const feedbackQuery = query(
      collection(db, 'feedback'),
      where('uid', '==', user.uid),
      orderBy('createdAt', 'desc'),
      limit(5),
    );
    const unsubFeedback = onSnapshot(
      feedbackQuery,
      (snapshot) => {
        setFeedbackList(snapshot.docs.map((d) => d.data() as StoredFeedback));
      },
      (error) => {
        handleFirestoreError(error, OperationType.LIST, feedbackPath);
      },
    );

    return () => {
      cancelled = true;
      unsubTarot();
      unsubFeedback();
    };
  }, [authReady, user]);

  const handleGoogleSignIn = async () => {
    setAuthError(null);
    try {
      await signInWithGoogle();
    } catch (error) {
      setAuthError(error instanceof Error ? error.message : 'Не удалось выполнить вход через Google.');
    }
  };

  const handleSaveProfile = async (e: FormEvent) => {
    e.preventDefault();
    if (!user) {
      return;
    }
    const cleanName = displayName.trim().slice(0, 100);
    const cleanDate = birthDate.trim();
    const cleanTime = birthTimeUnknown ? '' : birthTime.trim();
    const cleanPlace = birthPlace.trim().slice(0, 120);

    if (cleanName.length < 1) {
      setProfileNotice('Укажите имя (от 1 до 100 символов).');
      return;
    }
    if (!BIRTH_DATE_RE.test(cleanDate)) {
      setProfileNotice('Формат даты рождения: ГГГГ-ММ-ДД (или оставьте пустым).');
      return;
    }
    if (!BIRTH_TIME_RE.test(cleanTime)) {
      setProfileNotice('Формат времени рождения: ЧЧ:ММ (или отметьте «Время неизвестно»).');
      return;
    }

    setSavingProfile(true);
    setProfileNotice(null);
    const userPath = `users/${user.uid}`;
    const userRef = doc(db, 'users', user.uid);

    try {
      if (!profileExists) {
        await setDoc(userRef, {
          uid: user.uid,
          displayName: cleanName,
          birthDate: cleanDate,
          birthTime: cleanTime,
          birthTimeUnknown,
          birthPlace: cleanPlace,
          createdAt: serverTimestamp(),
          updatedAt: serverTimestamp(),
        });
        setProfileExists(true);
      } else {
        await updateDoc(userRef, {
          displayName: cleanName,
          birthDate: cleanDate,
          birthTime: cleanTime,
          birthTimeUnknown,
          birthPlace: cleanPlace,
          updatedAt: serverTimestamp(),
        });
      }
      setProfileNotice('Профиль сохранён в Cloud Firestore.');
    } catch (error) {
      handleFirestoreError(error, profileExists ? OperationType.UPDATE : OperationType.CREATE, userPath);
    } finally {
      setSavingProfile(false);
    }
  };

  const handleQuickTarotDraw = async () => {
    if (!user) {
      return;
    }
    setDrawingTarot(true);
    setProfileNotice(null);

    const userPath = `users/${user.uid}`;
    try {
      // Master Gate invariant: ensure parent user profile exists before writing subcollection
      if (!profileExists) {
        await setDoc(doc(db, 'users', user.uid), {
          uid: user.uid,
          displayName: (displayName.trim() || user.displayName || 'Пользователь').slice(0, 100),
          birthDate: BIRTH_DATE_RE.test(birthDate.trim()) ? birthDate.trim() : '',
          birthTime: birthTimeUnknown ? '' : BIRTH_TIME_RE.test(birthTime.trim()) ? birthTime.trim() : '',
          birthTimeUnknown,
          birthPlace: birthPlace.trim().slice(0, 120),
          createdAt: serverTimestamp(),
          updatedAt: serverTimestamp(),
        });
        setProfileExists(true);
      }
    } catch (error) {
      setDrawingTarot(false);
      handleFirestoreError(error, OperationType.CREATE, userPath);
    }

    const readingId = createDocId('tarot');
    const readingPath = `users/${user.uid}/tarotReadings/${readingId}`;
    const idx = crypto.getRandomValues(new Uint32Array(1))[0] % QUICK_TAROT_CARDS.length;
    const isReversed = (crypto.getRandomValues(new Uint32Array(1))[0] % 100) < 30;
    const card = QUICK_TAROT_CARDS[idx];
    const cleanQuestion = tarotQuestion.trim().slice(0, 300);

    try {
      await setDoc(doc(db, 'users', user.uid, 'tarotReadings', readingId), {
        readingId,
        uid: user.uid,
        spreadType: 'one_card',
        spreadTitle: 'Карта дня',
        question: cleanQuestion,
        cardsSummary: `${card.name} (${isReversed ? 'перевёрнутая' : 'прямая'})`,
        summary: (isReversed ? card.reversed : card.upright).slice(0, 1500),
        createdAt: serverTimestamp(),
      });
      setTarotQuestion('');
    } catch (error) {
      handleFirestoreError(error, OperationType.CREATE, readingPath);
    } finally {
      setDrawingTarot(false);
    }
  };

  const handleDeleteReading = async (readingId: string) => {
    if (!user) {
      return;
    }
    const readingPath = `users/${user.uid}/tarotReadings/${readingId}`;
    try {
      await deleteDoc(doc(db, 'users', user.uid, 'tarotReadings', readingId));
    } catch (error) {
      handleFirestoreError(error, OperationType.DELETE, readingPath);
    }
  };

  const handleSubmitFeedback = async (e: FormEvent) => {
    e.preventDefault();
    if (!user) {
      return;
    }
    const cleanMessage = feedbackText.trim().slice(0, 2000);
    if (cleanMessage.length < 5) {
      setFeedbackNotice('Напишите минимум 5 символов.');
      return;
    }

    setSendingFeedback(true);
    setFeedbackNotice(null);
    const feedbackId = createDocId('fb');
    const feedbackPath = `feedback/${feedbackId}`;

    try {
      await setDoc(doc(db, 'feedback', feedbackId), {
        feedbackId,
        uid: user.uid,
        message: cleanMessage,
        status: 'open',
        createdAt: serverTimestamp(),
      });
      setFeedbackText('');
      setFeedbackNotice('Обратная связь сохранена в Cloud Firestore.');
    } catch (error) {
      handleFirestoreError(error, OperationType.CREATE, feedbackPath);
    } finally {
      setSendingFeedback(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 antialiased selection:bg-indigo-500/30">
      <div className="mx-auto max-w-6xl px-6 py-8">
        <header className="flex flex-col gap-4 border-b border-slate-800/80 pb-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500/15 text-indigo-300 ring-1 ring-indigo-400/25">
              <Compass className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-2xl font-semibold tracking-tight text-white">Astralio</h1>
              <p className="text-xs text-slate-400">
                Telegram Bot MVP (Python 3.12+) · Firebase Firestore ({firebaseProjectMeta.projectId})
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {authReady && user ? (
              <>
                <span className="text-xs text-slate-300">{user.displayName || user.email}</span>
                <button
                  type="button"
                  onClick={() => void signOutUser()}
                  className="inline-flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs font-medium text-slate-200 hover:bg-slate-800"
                >
                  <LogOut className="h-3.5 w-3.5" />
                  Выйти
                </button>
              </>
            ) : (
              <button
                type="button"
                onClick={() => void handleGoogleSignIn()}
                className="inline-flex items-center gap-2 rounded-lg bg-indigo-500 px-4 py-2 text-xs font-medium text-white hover:bg-indigo-400"
              >
                <LogIn className="h-3.5 w-3.5" />
                Войти через Google (Firebase)
              </button>
            )}
          </div>
        </header>

        {authError && (
          <div className="mt-4 rounded-xl border border-rose-500/30 bg-rose-950/40 px-4 py-3 text-xs text-rose-200">
            {authError}
          </div>
        )}

        {/* Live Firebase Firestore Companion Workspace */}
        <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
          <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-base font-semibold text-white">
                Личный кабинет Astralio (Firebase Auth + Cloud Firestore)
              </h2>
              <p className="text-xs text-slate-400">
                База данных: <code className="text-indigo-300">{firebaseProjectMeta.firestoreDatabaseId}</code>
              </p>
            </div>
          </div>

          {!user ? (
            <div className="mt-4 rounded-xl border border-slate-800 bg-slate-950/70 p-5 text-sm text-slate-300">
              Войдите через Google, чтобы сохранять профиль рождения, историю раскладов Таро и обратную
              связь напрямую в защищённой базе Cloud Firestore.
            </div>
          ) : (
            <div className="mt-5 grid gap-6 lg:grid-cols-3">
              {/* Birth Profile Form */}
              <form
                onSubmit={(e) => void handleSaveProfile(e)}
                className="rounded-xl border border-slate-800 bg-slate-950/70 p-4"
              >
                <h3 className="flex items-center gap-2 text-sm font-semibold text-white">
                  <User className="h-4 w-4 text-indigo-300" />
                  Профиль рождения
                </h3>
                <div className="mt-3 space-y-3 text-xs">
                  <div>
                    <label className="block text-slate-400">Имя</label>
                    <input
                      type="text"
                      maxLength={100}
                      required
                      value={displayName}
                      onChange={(e) => setDisplayName(e.target.value)}
                      className="mt-1 w-full rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-slate-100 focus:border-indigo-400 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400">Дата рождения</label>
                    <input
                      type="date"
                      value={birthDate}
                      onChange={(e) => setBirthDate(e.target.value)}
                      className="mt-1 w-full rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-slate-100 focus:border-indigo-400 focus:outline-none"
                    />
                  </div>
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex-1">
                      <label className="block text-slate-400">Время (ЧЧ:ММ)</label>
                      <input
                        type="time"
                        disabled={birthTimeUnknown}
                        value={birthTimeUnknown ? '' : birthTime}
                        onChange={(e) => setBirthTime(e.target.value)}
                        className="mt-1 w-full rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-slate-100 disabled:opacity-40 focus:border-indigo-400 focus:outline-none"
                      />
                    </div>
                    <label className="mt-5 flex items-center gap-1.5 text-slate-300">
                      <input
                        type="checkbox"
                        checked={birthTimeUnknown}
                        onChange={(e) => setBirthTimeUnknown(e.target.checked)}
                        className="rounded border-slate-700 bg-slate-900"
                      />
                      Неизвестно
                    </label>
                  </div>
                  <div>
                    <label className="block text-slate-400">Место рождения</label>
                    <input
                      type="text"
                      maxLength={120}
                      placeholder="Москва"
                      value={birthPlace}
                      onChange={(e) => setBirthPlace(e.target.value)}
                      className="mt-1 w-full rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-slate-100 focus:border-indigo-400 focus:outline-none"
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={savingProfile}
                    className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-indigo-500 px-3 py-2 font-medium text-white hover:bg-indigo-400 disabled:opacity-60"
                  >
                    <Save className="h-3.5 w-3.5" />
                    {savingProfile ? 'Сохранение...' : 'Сохранить в Firestore'}
                  </button>
                  {profileNotice && <p className="text-emerald-300">{profileNotice}</p>}
                </div>
              </form>

              {/* Tarot Readings History */}
              <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
                <h3 className="flex items-center gap-2 text-sm font-semibold text-white">
                  <Layers className="h-4 w-4 text-indigo-300" />
                  Карта дня и история Таро
                </h3>
                <div className="mt-3 space-y-2 text-xs">
                  <input
                    type="text"
                    maxLength={300}
                    placeholder="Вопрос для расклада (необязательно)"
                    value={tarotQuestion}
                    onChange={(e) => setTarotQuestion(e.target.value)}
                    className="w-full rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-slate-100 focus:border-indigo-400 focus:outline-none"
                  />
                  <button
                    type="button"
                    disabled={drawingTarot}
                    onClick={() => void handleQuickTarotDraw()}
                    className="inline-flex w-full items-center justify-center gap-2 rounded-lg border border-indigo-400/40 bg-indigo-500/20 px-3 py-2 font-medium text-indigo-200 hover:bg-indigo-500/30 disabled:opacity-60"
                  >
                    <Sparkles className="h-3.5 w-3.5" />
                    {drawingTarot ? 'Вытягиваем карту...' : 'Вытянуть карту дня'}
                  </button>
                </div>

                <div className="mt-4 max-h-56 space-y-2 overflow-y-auto pr-1 text-xs">
                  {readings.length === 0 ? (
                    <p className="text-slate-500">История раскладов пока пуста.</p>
                  ) : (
                    readings.map((item) => (
                      <div
                        key={item.readingId}
                        className="rounded-lg border border-slate-800 bg-slate-900/70 p-2.5"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <span className="font-medium text-indigo-200">{item.cardsSummary}</span>
                          <button
                            type="button"
                            aria-label="Удалить расклад"
                            onClick={() => void handleDeleteReading(item.readingId)}
                            className="text-slate-500 hover:text-rose-400"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        </div>
                        {item.question && (
                          <p className="mt-0.5 text-[11px] italic text-slate-400">«{item.question}»</p>
                        )}
                        <p className="mt-1 text-slate-300">{item.summary}</p>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Feedback Form */}
              <form
                onSubmit={(e) => void handleSubmitFeedback(e)}
                className="rounded-xl border border-slate-800 bg-slate-950/70 p-4"
              >
                <h3 className="flex items-center gap-2 text-sm font-semibold text-white">
                  <HelpCircle className="h-4 w-4 text-indigo-300" />
                  Обратная связь
                </h3>
                <div className="mt-3 space-y-2 text-xs">
                  <textarea
                    rows={3}
                    minLength={5}
                    maxLength={2000}
                    placeholder="Напишите предложение или отзыв (от 5 символов)..."
                    value={feedbackText}
                    onChange={(e) => setFeedbackText(e.target.value)}
                    className="w-full rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-slate-100 focus:border-indigo-400 focus:outline-none"
                  />
                  <button
                    type="submit"
                    disabled={sendingFeedback}
                    className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-slate-800 px-3 py-2 font-medium text-slate-100 hover:bg-slate-700 disabled:opacity-60"
                  >
                    <Send className="h-3.5 w-3.5" />
                    {sendingFeedback ? 'Отправка...' : 'Отправить отзыв'}
                  </button>
                  {feedbackNotice && <p className="text-emerald-300">{feedbackNotice}</p>}
                </div>

                {feedbackList.length > 0 && (
                  <div className="mt-4 space-y-1.5 text-xs">
                    <p className="text-[11px] font-medium text-slate-400">Ваши сообщения:</p>
                    {feedbackList.map((fb) => (
                      <div
                        key={fb.feedbackId}
                        className="rounded-lg border border-slate-800 bg-slate-900/60 px-2.5 py-2 text-slate-300"
                      >
                        {fb.message}
                      </div>
                    ))}
                  </div>
                )}
              </form>
            </div>
          )}
        </section>

        {/* Telegram Bot MVP Architecture Explorer */}
        <main className="mt-8 grid gap-8 lg:grid-cols-12">
          <section className="lg:col-span-5">
            <h2 className="text-xs font-medium tracking-wider text-slate-400 uppercase">
              Telegram-бот Astralio (7 модулей)
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
                <h3 className="text-sm font-semibold">Конфигурация Firebase для Python-бота</h3>
              </div>
              <div className="mt-3 space-y-1.5 font-mono text-xs text-slate-300">
                <div>
                  <span className="text-slate-400">FIREBASE_PROJECT_ID=</span>
                  <span className="text-indigo-300">{firebaseProjectMeta.projectId}</span>
                </div>
                <div>
                  <span className="text-slate-400">FIREBASE_DATABASE_ID=</span>
                  <span className="text-indigo-300">{firebaseProjectMeta.firestoreDatabaseId}</span>
                </div>
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
