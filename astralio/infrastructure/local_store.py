"""Local JSON-file Firestore-compatible store for local / AI Studio preview execution.

Used ONLY when Firebase Admin SDK service account credentials are not configured
(for example, when running locally inside Google AI Studio with only BOT_TOKEN).
Production deployments with FIREBASE_PROJECT_ID, FIREBASE_CLIENT_EMAIL, and
FIREBASE_PRIVATE_KEY always use real Google Cloud Firestore.
"""

from __future__ import annotations

import json
import threading
from copy import deepcopy
from pathlib import Path
from typing import Any


class AlreadyExists(Exception):
    """Raised when attempting to create a document ID that already exists."""


class _LocalDocumentSnapshot:
    def __init__(self, doc_id: str, data: dict[str, Any] | None) -> None:
        self.id = doc_id
        self._data = deepcopy(data) if data is not None else None

    @property
    def exists(self) -> bool:
        return self._data is not None

    def to_dict(self) -> dict[str, Any] | None:
        return deepcopy(self._data) if self._data is not None else None


class _LocalQuery:
    def __init__(
        self,
        docs: list[_LocalDocumentSnapshot],
        order_field: str | None = None,
        descending: bool = False,
        limit_n: int | None = None,
    ) -> None:
        self._docs = docs
        self._order_field = order_field
        self._descending = descending
        self._limit = limit_n

    def order_by(self, field: str, direction: str = "ASCENDING") -> _LocalQuery:
        return _LocalQuery(
            self._docs,
            order_field=field,
            descending=(direction.upper() == "DESCENDING"),
            limit_n=self._limit,
        )

    def limit(self, count: int) -> _LocalQuery:
        return _LocalQuery(
            self._docs,
            order_field=self._order_field,
            descending=self._descending,
            limit_n=count,
        )

    def stream(self) -> list[_LocalDocumentSnapshot]:
        items = list(self._docs)
        if self._order_field:
            items.sort(
                key=lambda snap: (snap.to_dict() or {}).get(self._order_field, ""),
                reverse=self._descending,
            )
        if self._limit is not None:
            items = items[: self._limit]
        return items


class _LocalDocumentReference:
    def __init__(self, client: LocalFileFirestoreClient, path: str, doc_id: str) -> None:
        self._client = client
        self._path = path
        self.id = doc_id

    def get(self) -> _LocalDocumentSnapshot:
        return _LocalDocumentSnapshot(self.id, self._client.read_doc(self._path))

    def set(self, data: dict[str, Any], merge: bool = False) -> None:
        self._client.write_doc(self._path, data, merge=merge)

    def create(self, data: dict[str, Any]) -> None:
        self._client.create_doc(self._path, data)

    def collection(self, name: str) -> _LocalCollectionReference:
        return _LocalCollectionReference(self._client, f"{self._path}/{name}")


class _LocalCollectionReference:
    def __init__(self, client: LocalFileFirestoreClient, prefix: str) -> None:
        self._client = client
        self._prefix = prefix

    def document(self, doc_id: str) -> _LocalDocumentReference:
        return _LocalDocumentReference(self._client, f"{self._prefix}/{doc_id}", doc_id)

    def _direct_docs(self) -> list[_LocalDocumentSnapshot]:
        return [
            _LocalDocumentSnapshot(doc_id, data)
            for doc_id, data in self._client.list_direct_children(self._prefix)
        ]

    def order_by(self, field: str, direction: str = "ASCENDING") -> _LocalQuery:
        return _LocalQuery(self._direct_docs()).order_by(field, direction=direction)

    def limit(self, count: int) -> _LocalQuery:
        return _LocalQuery(self._direct_docs()).limit(count)

    def stream(self) -> list[_LocalDocumentSnapshot]:
        return self._direct_docs()


class LocalFileFirestoreClient:
    """Thread-safe JSON-backed Firestore-compatible client for local preview execution."""

    def __init__(self, file_path: str | Path = ".astralio_local_db.json") -> None:
        self._path = Path(file_path)
        self._lock = threading.Lock()
        self._store: dict[str, dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                self._store = raw
        except Exception:
            self._store = {}

    def _persist(self) -> None:
        tmp_path = self._path.with_suffix(".tmp")
        tmp_path.write_text(
            json.dumps(self._store, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp_path.replace(self._path)

    def read_doc(self, path: str) -> dict[str, Any] | None:
        with self._lock:
            return deepcopy(self._store.get(path))

    def write_doc(self, path: str, data: dict[str, Any], *, merge: bool = False) -> None:
        with self._lock:
            if merge and path in self._store:
                merged = deepcopy(self._store[path])
                merged.update(deepcopy(data))
                self._store[path] = merged
            else:
                self._store[path] = deepcopy(data)
            self._persist()

    def create_doc(self, path: str, data: dict[str, Any]) -> None:
        with self._lock:
            if path in self._store:
                raise AlreadyExists(f"Document {path} already exists.")
            self._store[path] = deepcopy(data)
            self._persist()

    def list_direct_children(self, prefix: str) -> list[tuple[str, dict[str, Any]]]:
        prefix_slash = f"{prefix}/"
        with self._lock:
            results: list[tuple[str, dict[str, Any]]] = []
            for key, value in self._store.items():
                if key.startswith(prefix_slash):
                    remainder = key[len(prefix_slash) :]
                    if "/" not in remainder:
                        results.append((remainder, deepcopy(value)))
            return results

    def collection(self, name: str) -> _LocalCollectionReference:
        return _LocalCollectionReference(self, name)
