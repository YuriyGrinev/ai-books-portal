from typing import List, Optional, UUID
import aiohttp
from ...domain.interfaces.notification import NotificationService
from ...domain.entities.user import User
from ...domain.entities.comment import Comment
from ...infrastructure.config.settings import settings


class TelegramNotificationService(NotificationService):
    def __init__(self, bot_token: str, admin_chat_ids: List[str]):
        self.bot_token = bot_token
        self.admin_chat_ids = admin_chat_ids
        self.api_url = f"https://api.telegram.org/bot{bot_token}"

    async def _send_message(self, message: str) -> None:
        """Отправляет сообщение всем администраторам."""
        async with aiohttp.ClientSession() as session:
            for chat_id in self.admin_chat_ids:
                try:
                    async with session.post(
                        f"{self.api_url}/sendMessage",
                        json={
                            "chat_id": chat_id,
                            "text": message,
                            "parse_mode": "HTML"
                        }
                    ) as response:
                        if response.status != 200:
                            # В реальном приложении здесь должно быть логирование
                            pass
                except Exception as e:
                    # В реальном приложении здесь должно быть логирование
                    pass

    async def notify_new_user(self, user: User) -> None:
        """Уведомляет о регистрации нового пользователя."""
        message = (
            f"🆕 <b>Новый пользователь</b>\n"
            f"ID: <code>{user.id}</code>\n"
            f"Email: <code>{user.email}</code>\n"
            f"Username: <code>{user.username}</code>"
        )
        await self._send_message(message)

    async def notify_user_blocked(self, user: User, reason: str) -> None:
        """Уведомляет о блокировке пользователя."""
        message = (
            f"🚫 <b>Пользователь заблокирован</b>\n"
            f"ID: <code>{user.id}</code>\n"
            f"Email: <code>{user.email}</code>\n"
            f"Username: <code>{user.username}</code>\n"
            f"Причина: {reason}"
        )
        await self._send_message(message)

    async def notify_user_unblocked(self, user: User) -> None:
        """Уведомляет о разблокировке пользователя."""
        message = (
            f"✅ <b>Пользователь разблокирован</b>\n"
            f"ID: <code>{user.id}</code>\n"
            f"Email: <code>{user.email}</code>\n"
            f"Username: <code>{user.username}</code>"
        )
        await self._send_message(message)

    async def notify_role_changed(self, user: User, old_role: str, new_role: str) -> None:
        """Уведомляет об изменении роли пользователя."""
        message = (
            f"👤 <b>Изменение роли пользователя</b>\n"
            f"ID: <code>{user.id}</code>\n"
            f"Email: <code>{user.email}</code>\n"
            f"Username: <code>{user.username}</code>\n"
            f"Старая роль: {old_role}\n"
            f"Новая роль: {new_role}"
        )
        await self._send_message(message)

    async def notify_comment_reported(self, comment: Comment, reason: str) -> None:
        """Уведомляет о жалобе на комментарий."""
        message = (
            f"⚠️ <b>Жалоба на комментарий</b>\n"
            f"ID комментария: <code>{comment.id}</code>\n"
            f"Автор: <code>{comment.user.username}</code>\n"
            f"Книга: {comment.book.title}\n"
            f"Содержание: {comment.content}\n"
            f"Причина жалобы: {reason}"
        )
        await self._send_message(message)

    async def notify_comment_moderated(
        self, comment: Comment, action: str, reason: str
    ) -> None:
        """Уведомляет о модерации комментария."""
        message = (
            f"🛡 <b>Модерация комментария</b>\n"
            f"ID комментария: <code>{comment.id}</code>\n"
            f"Автор: <code>{comment.user.username}</code>\n"
            f"Книга: {comment.book.title}\n"
            f"Действие: {action}\n"
            f"Причина: {reason}"
        )
        await self._send_message(message)

    async def notify_system_error(self, error: str, details: Optional[str] = None) -> None:
        """Уведомляет о системной ошибке."""
        message = (
            f"🚨 <b>Системная ошибка</b>\n"
            f"Ошибка: {error}"
        )
        if details:
            message += f"\nДетали: {details}"
        await self._send_message(message) 