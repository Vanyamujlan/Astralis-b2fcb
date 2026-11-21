"""User registration, profile formatting, and birth data updates."""

from __future__ import annotations

from datetime import UTC, date, datetime, time

from astralio.infrastructure.geocoding import GeocodingService
from astralio.models.astrology import GeoLocation
from astralio.models.user import BirthData, UserProfile
from astralio.repositories.user_repository import UserRepository


class UserService:
    """Coordinates user registration, profile retrieval, and validated birth data edits."""

    def __init__(
        self,
        user_repository: UserRepository,
        geocoding_service: GeocodingService,
    ) -> None:
        self._user_repo = user_repository
        self._geocoding = geocoding_service

    async def ensure_registered(
        self,
        *,
        telegram_id: int,
        first_name: str,
        last_name: str | None = None,
        username: str | None = None,
    ) -> tuple[UserProfile, bool]:
        """Automatically register or sync a Telegram user in Firestore."""
        return await self._user_repo.get_or_create_user(
            telegram_id=telegram_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
        )

    async def get_profile(self, telegram_id: int) -> UserProfile | None:
        return await self._user_repo.get_user(telegram_id)

    async def save_birth_data(self, telegram_id: int, birth_data: BirthData) -> UserProfile:
        return await self._user_repo.update_birth_data(telegram_id, birth_data)

    async def update_birth_date(self, telegram_id: int, birth_date: date) -> UserProfile:
        user = await self._user_repo.get_user(telegram_id)
        birth = user.birth_data.model_copy() if user else BirthData()
        birth.birth_date = birth_date
        return await self._user_repo.update_birth_data(telegram_id, birth)

    async def update_birth_time(
        self,
        telegram_id: int,
        birth_time: time | None,
        *,
        is_unknown: bool = False,
    ) -> UserProfile:
        user = await self._user_repo.get_user(telegram_id)
        birth = user.birth_data.model_copy() if user else BirthData()
        birth.birth_time = None if is_unknown else birth_time
        birth.birth_time_unknown = is_unknown
        return await self._user_repo.update_birth_data(telegram_id, birth)

    async def resolve_place(self, place_query: str) -> GeoLocation | None:
        return await self._geocoding.resolve(place_query)

    async def update_birth_place(
        self,
        telegram_id: int,
        location: GeoLocation,
    ) -> UserProfile:
        user = await self._user_repo.get_user(telegram_id)
        birth = user.birth_data.model_copy() if user else BirthData()
        birth.birth_place = location.name
        birth.latitude = location.latitude
        birth.longitude = location.longitude
        birth.timezone = location.timezone
        return await self._user_repo.update_birth_data(telegram_id, birth)

    def format_profile(self, profile: UserProfile) -> str:
        """Render user profile overview in clean minimalist HTML."""
        birth = profile.birth_data
        username_str = f"@{profile.username}" if profile.username else "не указан"
        date_str = birth.birth_date.strftime("%d.%m.%Y") if birth.birth_date else "не указана"
        if birth.birth_time_unknown:
            time_str = "неизвестно (расчёт без домов)"
        elif birth.birth_time is not None:
            time_str = birth.birth_time.strftime("%H:%M")
        else:
            time_str = "не указано"

        place_str = birth.birth_place or "не указано"
        coords_str = (
            f" ({birth.latitude:.2f}, {birth.longitude:.2f}, {birth.timezone})"
            if birth.has_coordinates and birth.latitude is not None and birth.longitude is not None
            else ""
        )

        sub_active = profile.subscription.is_currently_active(datetime.now(UTC))
        if sub_active and profile.subscription.expires_at is not None:
            sub_str = f"Premium (до {profile.subscription.expires_at.strftime('%d.%m.%Y')})"
        else:
            sub_str = "Базовый (бесплатный)"

        return "\n".join(
            [
                "👤 <b>Профиль Astralio</b>",
                "",
                f"• Имя: {profile.display_name}",
                f"• Username: {username_str}",
                f"• Telegram ID: <code>{profile.telegram_id}</code>",
                "",
                "<b>Данные рождения:</b>",
                f"• Дата: {date_str}",
                f"• Время: {time_str}",
                f"• Место: {place_str}{coords_str}",
                "",
                f"⭐ Подписка: {sub_str}",
            ]
        )
