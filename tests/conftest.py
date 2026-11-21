"""Shared pytest fixtures, in-memory Firestore mock, and Telegram Update factories."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock

import pytest
from telegram import (
    CallbackQuery,
    Chat,
    Message,
    MessageEntity,
    PreCheckoutQuery,
    SuccessfulPayment,
    Update,
    User,
)

from astralio.app import build_application, build_service_container
from astralio.config import Settings
from astralio.handlers.deps import ServiceContainer
from astralio.infrastructure.geocoding import GeocodingService


class AlreadyExists(Exception):
    """Mimics google.api_core.exceptions.AlreadyExists for idempotency tests."""


class FakeDocumentSnapshot:
    def __init__(self, doc_id: str, data: dict[str, Any] | None) -> None:
        self.id = doc_id
        self._data = deepcopy(data) if data is not None else None

    @property
    def exists(self) -> bool:
        return self._data is not None

    def to_dict(self) -> dict[str, Any] | None:
        return deepcopy(self._data) if self._data is not None else None


class FakeQuery:
    def __init__(
        self,
        docs: list[FakeDocumentSnapshot],
        order_field: str | None = None,
        descending: bool = False,
        limit_n: int | None = None,
    ) -> None:
        self._docs = docs
        self._order_field = order_field
        self._descending = descending
        self._limit = limit_n

    def order_by(self, field: str, direction: str = "ASCENDING") -> FakeQuery:
        return FakeQuery(
            self._docs,
            order_field=field,
            descending=(direction.upper() == "DESCENDING"),
            limit_n=self._limit,
        )

    def limit(self, count: int) -> FakeQuery:
        return FakeQuery(
            self._docs,
            order_field=self._order_field,
            descending=self._descending,
            limit_n=count,
        )

    def stream(self) -> list[FakeDocumentSnapshot]:
        items = list(self._docs)
        if self._order_field:
            items.sort(
                key=lambda snap: (snap.to_dict() or {}).get(self._order_field, ""),
                reverse=self._descending,
            )
        if self._limit is not None:
            items = items[: self._limit]
        return items


class FakeDocumentReference:
    def __init__(self, store: dict[str, dict[str, Any]], path: str, doc_id: str) -> None:
        self._store = store
        self._path = path
        self.id = doc_id

    def get(self) -> FakeDocumentSnapshot:
        return FakeDocumentSnapshot(self.id, self._store.get(self._path))

    def set(self, data: dict[str, Any], merge: bool = False) -> None:
        if merge and self._path in self._store:
            merged = deepcopy(self._store[self._path])
            merged.update(deepcopy(data))
            self._store[self._path] = merged
        else:
            self._store[self._path] = deepcopy(data)

    def create(self, data: dict[str, Any]) -> None:
        if self._path in self._store:
            raise AlreadyExists(f"Document {self._path} already exists")
        self._store[self._path] = deepcopy(data)

    def collection(self, name: str) -> FakeCollectionReference:
        return FakeCollectionReference(self._store, f"{self._path}/{name}")


class FakeCollectionReference:
    def __init__(self, store: dict[str, dict[str, Any]], prefix: str) -> None:
        self._store = store
        self._prefix = prefix

    def document(self, doc_id: str) -> FakeDocumentReference:
        return FakeDocumentReference(self._store, f"{self._prefix}/{doc_id}", doc_id)

    def _direct_docs(self) -> list[FakeDocumentSnapshot]:
        prefix_slash = f"{self._prefix}/"
        docs: list[FakeDocumentSnapshot] = []
        for key, value in self._store.items():
            if key.startswith(prefix_slash):
                remainder = key[len(prefix_slash) :]
                if "/" not in remainder:
                    docs.append(FakeDocumentSnapshot(remainder, value))
        return docs

    def order_by(self, field: str, direction: str = "ASCENDING") -> FakeQuery:
        return FakeQuery(self._direct_docs()).order_by(field, direction=direction)

    def limit(self, count: int) -> FakeQuery:
        return FakeQuery(self._direct_docs()).limit(count)

    def stream(self) -> list[FakeDocumentSnapshot]:
        return self._direct_docs()


class FakeFirestoreClient:
    """In-memory Firestore mock supporting collections, subcollections, merge, create, and queries."""

    def __init__(self) -> None:
        self.store: dict[str, dict[str, Any]] = {}

    def collection(self, name: str) -> FakeCollectionReference:
        return FakeCollectionReference(self.store, name)


@pytest.fixture
def fake_db() -> FakeFirestoreClient:
    return FakeFirestoreClient()


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        BOT_TOKEN="123456789:AAFakeTestTokenForPytestOnly1234567890",
        FIREBASE_PROJECT_ID="astralio-test-project",
        FIREBASE_CLIENT_EMAIL="test@astralio-test-project.iam.gserviceaccount.com",
        FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\\nTESTKEY\\n-----END PRIVATE KEY-----\\n",
        FIREBASE_DATABASE_ID="",
        AI_API_KEY="",
        TELEGRAM_STARS_ENABLED=False,
        GEOCODING_ENABLED=False,
        LOG_LEVEL="WARNING",
    )


@pytest.fixture
def services(test_settings: Settings, fake_db: FakeFirestoreClient) -> ServiceContainer:
    return build_service_container(test_settings, firestore_client=fake_db)


@pytest.fixture
def geocoding_service() -> GeocodingService:
    return GeocodingService(remote_enabled=False)


class MockBotRecorder:
    """Captures outgoing Telegram messages, edits, answers, and invoices during end-to-end tests."""

    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []
        self.sent_messages: list[dict[str, Any]] = []
        self.edited_messages: list[dict[str, Any]] = []
        self.answered_callbacks: list[dict[str, Any]] = []
        self.sent_invoices: list[dict[str, Any]] = []
        self.pre_checkout_answers: list[dict[str, Any]] = []
        self._msg_id = 100

    @property
    def last_text(self) -> str:
        assert self.events, "Expected at least one outgoing bot message or edit."
        return str(self.events[-1]["text"])

    def next_message_id(self) -> int:
        self._msg_id += 1
        return self._msg_id


def attach_mock_bot(app: Any) -> MockBotRecorder:
    """Replace network Bot API methods on a real PTB Application with in-memory AsyncMocks."""
    recorder = MockBotRecorder()
    bot = app.bot

    async def _send_message(chat_id: int, text: str, **kwargs: Any) -> Message:
        event = {"kind": "send", "chat_id": chat_id, "text": text, **kwargs}
        recorder.events.append(event)
        recorder.sent_messages.append(event)
        msg = Message(
            message_id=recorder.next_message_id(),
            date=datetime.now(UTC),
            chat=Chat(id=chat_id, type="private"),
            text=text,
        )
        msg.set_bot(bot)
        return msg

    async def _edit_message_text(text: str, **kwargs: Any) -> Message:
        event = {"kind": "edit", "text": text, **kwargs}
        recorder.events.append(event)
        recorder.edited_messages.append(event)
        chat_id = kwargs.get("chat_id", 1)
        msg = Message(
            message_id=kwargs.get("message_id", recorder.next_message_id()),
            date=datetime.now(UTC),
            chat=Chat(id=chat_id, type="private"),
            text=text,
        )
        msg.set_bot(bot)
        return msg

    async def _answer_callback_query(callback_query_id: str, **kwargs: Any) -> bool:
        recorder.answered_callbacks.append({"id": callback_query_id, **kwargs})
        return True

    async def _send_invoice(**kwargs: Any) -> Message:
        recorder.sent_invoices.append(kwargs)
        msg = Message(
            message_id=recorder.next_message_id(),
            date=datetime.now(UTC),
            chat=Chat(id=kwargs["chat_id"], type="private"),
            text="[invoice]",
        )
        msg.set_bot(bot)
        return msg

    async def _answer_pre_checkout_query(
        pre_checkout_query_id: str, ok: bool, **kwargs: Any
    ) -> bool:
        recorder.pre_checkout_answers.append({"id": pre_checkout_query_id, "ok": ok, **kwargs})
        return True

    object.__setattr__(bot, "_initialized", True)
    object.__setattr__(
        bot,
        "_bot_user",
        User(id=999000, first_name="Astralio", is_bot=True, username="astralio_test_bot"),
    )
    object.__setattr__(bot, "initialize", AsyncMock(return_value=None))
    object.__setattr__(bot, "shutdown", AsyncMock(return_value=None))
    object.__setattr__(bot, "send_message", AsyncMock(side_effect=_send_message))
    object.__setattr__(bot, "edit_message_text", AsyncMock(side_effect=_edit_message_text))
    object.__setattr__(bot, "answer_callback_query", AsyncMock(side_effect=_answer_callback_query))
    object.__setattr__(bot, "send_invoice", AsyncMock(side_effect=_send_invoice))
    object.__setattr__(
        bot,
        "answer_pre_checkout_query",
        AsyncMock(side_effect=_answer_pre_checkout_query),
    )
    object.__setattr__(bot, "set_my_commands", AsyncMock(return_value=True))
    app._initialized = True
    return recorder


def make_text_update(
    bot: Any,
    text: str,
    *,
    user_id: int = 1001,
    first_name: str = "Анна",
    username: str = "anna_star",
    update_id: int = 1,
) -> Update:
    user = User(id=user_id, first_name=first_name, is_bot=False, username=username)
    chat = Chat(id=user_id, type="private")
    entities: tuple[MessageEntity, ...] = ()
    if text.startswith("/"):
        cmd_len = len(text.split()[0])
        entities = (MessageEntity(type=MessageEntity.BOT_COMMAND, offset=0, length=cmd_len),)
    message = Message(
        message_id=update_id + 10,
        date=datetime.now(UTC),
        chat=chat,
        from_user=user,
        text=text,
        entities=entities,
    )
    message.set_bot(bot)
    return Update(update_id=update_id, message=message)


def make_callback_update(
    bot: Any,
    data: str,
    *,
    user_id: int = 1001,
    first_name: str = "Анна",
    username: str = "anna_star",
    update_id: int = 2,
) -> Update:
    user = User(id=user_id, first_name=first_name, is_bot=False, username=username)
    chat = Chat(id=user_id, type="private")
    origin_msg = Message(
        message_id=50,
        date=datetime.now(UTC),
        chat=chat,
        from_user=user,
        text="menu",
    )
    origin_msg.set_bot(bot)
    query = CallbackQuery(
        id=f"cbq_{update_id}",
        from_user=user,
        chat_instance=str(user_id),
        message=origin_msg,
        data=data,
    )
    query.set_bot(bot)
    return Update(update_id=update_id, callback_query=query)


def make_pre_checkout_update(
    bot: Any,
    *,
    payload: str,
    currency: str = "XTR",
    total_amount: int = 199,
    user_id: int = 1001,
    update_id: int = 50,
) -> Update:
    user = User(id=user_id, first_name="Анна", is_bot=False, username="anna_star")
    query = PreCheckoutQuery(
        id=f"pcq_{update_id}",
        from_user=user,
        currency=currency,
        total_amount=total_amount,
        invoice_payload=payload,
    )
    query.set_bot(bot)
    return Update(update_id=update_id, pre_checkout_query=query)


def make_successful_payment_update(
    bot: Any,
    *,
    payload: str,
    charge_id: str,
    currency: str = "XTR",
    total_amount: int = 199,
    user_id: int = 1001,
    update_id: int = 51,
) -> Update:
    user = User(id=user_id, first_name="Анна", is_bot=False, username="anna_star")
    chat = Chat(id=user_id, type="private")
    payment = SuccessfulPayment(
        currency=currency,
        total_amount=total_amount,
        invoice_payload=payload,
        telegram_payment_charge_id=charge_id,
        provider_payment_charge_id="provider_stars",
    )
    msg = Message(
        message_id=update_id + 10,
        date=datetime.now(UTC),
        chat=chat,
        from_user=user,
        successful_payment=payment,
    )
    msg.set_bot(bot)
    return Update(update_id=update_id, message=msg)


@pytest.fixture
def wired_app(test_settings: Settings, fake_db: FakeFirestoreClient) -> tuple[Any, MockBotRecorder]:
    app = build_application(test_settings, firestore_client=fake_db)
    recorder = attach_mock_bot(app)
    return app, recorder
