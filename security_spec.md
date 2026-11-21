# Astralio Firestore Security Specification (Phase 0 TDD)

## 1. Data Invariants
1. **Default Deny**: All unspecified Firestore paths deny read and write access (`match /{document=**} { allow read, write: if false; }`).
2. **Verified Identity**: All writes require an authenticated, email-verified Firebase user (`request.auth != null && request.auth.token.email_verified == true`).
3. **Strict Owner Isolation (PII)**: `/users/{userId}` can only be read, created, or updated by `request.auth.uid == userId`. No blanket `isSignedIn()` reads or list queries are allowed on `/users`.
4. **Master Gate on Subcollections**: `/users/{userId}/tarotReadings/{readingId}` requires `exists(/databases/$(database)/documents/users/$(userId))` on create/update/delete, and strict `resource.data.uid == request.auth.uid` on `list`.
5. **Anti-Update-Gap & Immutability**: Every `create` and `update` invokes its `isValid[Entity](incoming())` blueprint helper. Immutable fields (`uid`, `createdAt`, `readingId`, `feedbackId`) cannot change on update. Server timestamps (`request.time`) are mandatory on `createdAt` (create) and `updatedAt` (update).
6. **No Ghost Fields & Strict Size Bounds**: Every `create` checks `hasAll` + `hasOnly`. Every `update` checks `affectedKeys().hasOnly(...)`. Every string has an explicit `.size()` upper bound and ID regex guard `^[a-zA-Z0-9_\\-]+$`.
7. **Feedback Terminal Integrity**: `/feedback/{feedbackId}` must be created with `status == 'open'`, cannot be modified or deleted by clients, and can only be read/listed by its author (`resource.data.uid == request.auth.uid`).

## 2. The "Dirty Dozen" Adversarial Payloads (Must ALL return PERMISSION_DENIED)
1. **Unauthenticated Read** (`GET /users/alice` with `auth = null`) -> DENIED.
2. **Cross-User PII Read** (`GET /users/alice` as `uid = bob`) -> DENIED.
3. **Unverified Email Write** (`CREATE /users/alice` with `email_verified = false`) -> DENIED.
4. **Identity Spoofing on Create** (`CREATE /users/alice` with `uid: "bob"`) -> DENIED.
5. **Shadow / Ghost Field Injection** (`CREATE /users/alice` including `isAdmin: true` or `plan: "premium"`) -> DENIED.
6. **Client-Forged Timestamp** (`CREATE /users/alice` with `createdAt` != `request.time`) -> DENIED.
7. **Oversized String / Resource Poisoning** (`UPDATE /users/alice` with `birthPlace` of 5,000 chars) -> DENIED.
8. **Malformed Path Document ID** (`CREATE /users/alice/tarotReadings/bad$id!` with invalid characters) -> DENIED.
9. **Orphaned Tarot Reading (Master Gate Bypass)** (`CREATE /users/alice/tarotReadings/r1` when `/users/alice` does not exist) -> DENIED.
10. **Immutable Field Mutation** (`UPDATE /users/alice` attempting to alter `createdAt` or `uid`) -> DENIED.
11. **Feedback Status Forgery** (`CREATE /feedback/f1` with `status: "reviewed"`) -> DENIED.
12. **Blanket Feedback List Scraping** (`LIST /feedback` without `where("uid", "==", request.auth.uid)`) -> DENIED.
