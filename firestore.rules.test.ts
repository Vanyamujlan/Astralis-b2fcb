/**
 * Security specification test blueprint for Astralio Firestore Rules (Phase 0 TDD).
 * Documents the "Dirty Dozen" adversarial payloads that must return PERMISSION_DENIED.
 */

export interface DirtyDozenCase {
  id: number;
  name: string;
  operation: 'get' | 'list' | 'create' | 'update' | 'delete';
  path: string;
  authUid: string | null;
  emailVerified: boolean;
  payload?: Record<string, unknown>;
  expected: 'PERMISSION_DENIED';
}

export const DIRTY_DOZEN_CASES: DirtyDozenCase[] = [
  {
    id: 1,
    name: 'Unauthenticated read on user profile',
    operation: 'get',
    path: '/users/alice',
    authUid: null,
    emailVerified: false,
    expected: 'PERMISSION_DENIED',
  },
  {
    id: 2,
    name: 'Cross-user PII read attempt',
    operation: 'get',
    path: '/users/alice',
    authUid: 'bob',
    emailVerified: true,
    expected: 'PERMISSION_DENIED',
  },
  {
    id: 3,
    name: 'Unverified email write attempt',
    operation: 'create',
    path: '/users/alice',
    authUid: 'alice',
    emailVerified: false,
    payload: {
      uid: 'alice',
      displayName: 'Alice',
      birthDate: '1995-05-15',
      birthTime: '14:30',
      birthTimeUnknown: false,
      birthPlace: 'Москва',
    },
    expected: 'PERMISSION_DENIED',
  },
  {
    id: 4,
    name: 'Identity spoofing in uid field',
    operation: 'create',
    path: '/users/alice',
    authUid: 'alice',
    emailVerified: true,
    payload: {
      uid: 'bob',
      displayName: 'Alice',
      birthDate: '1995-05-15',
      birthTime: '14:30',
      birthTimeUnknown: false,
      birthPlace: 'Москва',
    },
    expected: 'PERMISSION_DENIED',
  },
  {
    id: 5,
    name: 'Shadow / ghost privilege field injection',
    operation: 'create',
    path: '/users/alice',
    authUid: 'alice',
    emailVerified: true,
    payload: {
      uid: 'alice',
      displayName: 'Alice',
      birthDate: '1995-05-15',
      birthTime: '14:30',
      birthTimeUnknown: false,
      birthPlace: 'Москва',
      isAdmin: true,
    },
    expected: 'PERMISSION_DENIED',
  },
  {
    id: 6,
    name: 'Client-forged createdAt timestamp',
    operation: 'create',
    path: '/users/alice',
    authUid: 'alice',
    emailVerified: true,
    payload: {
      uid: 'alice',
      displayName: 'Alice',
      birthDate: '1995-05-15',
      birthTime: '14:30',
      birthTimeUnknown: false,
      birthPlace: 'Москва',
      createdAt: '2020-01-01T00:00:00Z',
      updatedAt: '2020-01-01T00:00:00Z',
    },
    expected: 'PERMISSION_DENIED',
  },
  {
    id: 7,
    name: 'Oversized string resource poisoning',
    operation: 'update',
    path: '/users/alice',
    authUid: 'alice',
    emailVerified: true,
    payload: {
      birthPlace: 'A'.repeat(5000),
    },
    expected: 'PERMISSION_DENIED',
  },
  {
    id: 8,
    name: 'Malformed document ID poisoning',
    operation: 'create',
    path: '/users/alice/tarotReadings/bad$id!with*symbols',
    authUid: 'alice',
    emailVerified: true,
    payload: {
      readingId: 'bad$id!with*symbols',
      uid: 'alice',
      spreadType: 'one_card',
      spreadTitle: 'Карта дня',
      question: '',
      cardsSummary: 'Шут (прямая)',
      summary: 'Новое начало.',
    },
    expected: 'PERMISSION_DENIED',
  },
  {
    id: 9,
    name: 'Orphaned Tarot reading without parent profile (Master Gate)',
    operation: 'create',
    path: '/users/ghostUser/tarotReadings/r_001',
    authUid: 'ghostUser',
    emailVerified: true,
    payload: {
      readingId: 'r_001',
      uid: 'ghostUser',
      spreadType: 'one_card',
      spreadTitle: 'Карта дня',
      question: '',
      cardsSummary: 'Шут (прямая)',
      summary: 'Новое начало.',
    },
    expected: 'PERMISSION_DENIED',
  },
  {
    id: 10,
    name: 'Immutable createdAt mutation on profile update',
    operation: 'update',
    path: '/users/alice',
    authUid: 'alice',
    emailVerified: true,
    payload: {
      createdAt: '2000-01-01T00:00:00Z',
    },
    expected: 'PERMISSION_DENIED',
  },
  {
    id: 11,
    name: 'Feedback status forgery on creation',
    operation: 'create',
    path: '/feedback/fb_001',
    authUid: 'alice',
    emailVerified: true,
    payload: {
      feedbackId: 'fb_001',
      uid: 'alice',
      message: 'Valid length feedback message',
      status: 'reviewed',
    },
    expected: 'PERMISSION_DENIED',
  },
  {
    id: 12,
    name: 'Blanket list query scraping other users feedback',
    operation: 'list',
    path: '/feedback',
    authUid: 'bob',
    emailVerified: true,
    expected: 'PERMISSION_DENIED',
  },
];
