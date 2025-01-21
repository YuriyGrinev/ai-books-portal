from typing import List, Optional
from uuid import UUID

import aiohttp

from books_portal.domain.interfaces.notifications import NotificationService
from books_portal.infrastructure.config.settings import settings


class TelegramNotificationService(NotificationService):
    """Сервис уведомлений через Telegram"""

    def __init__(self) -> None:
        """Инициализация сервиса"""
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.admin_chat_ids = settings.TELEGRAM_ADMIN_CHAT_IDS
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    async def _send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = "HTML",
        disable_web_page_preview: bool = True,
    ) -> None:
        """Отправка сообщения"""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": disable_web_page_preview,
            }
            async with session.post(url, json=data) as response:
                if not response.ok:
                    error_data = await response.json()
                    raise RuntimeError(f"Failed to send Telegram message: {error_data}")

    async def notify_new_user(
        self,
        user_id: UUID,
        email: str,
        username: str,
    ) -> None:
        """Уведомление о новом пользователе"""
        message = (
            f"🆕 <b>Новый пользователь</b>\n\n"
            f"ID: <code>{user_id}</code>\n"
            f"Email: <code>{email}</code>\n"
            f"Username: <code>{username}</code>"
        )
        
        for chat_id in self.admin_chat_ids:
            await self._send_message(chat_id, message)

    async def notify_user_blocked(
        self,
        user_id: UUID,
        email: str,
        username: str,
        reason: str,
        admin_username: str,
    ) -> None:
        """Уведомление о блокировке пользователя"""
        message = (
            f"🚫 <b>Пользователь заблокирован</b>\n\n"
            f"ID: <code>{user_id}</code>\n"
            f"Email: <code>{email}</code>\n"
            f"Username: <code>{username}</code>\n"
            f"Причина: {reason}\n"
            f"Администратор: <code>{admin_username}</code>"
        )
        
        for chat_id in self.admin_chat_ids:
            await self._send_message(chat_id, message)

    async def notify_user_unblocked(
        self,
        user_id: UUID,
        email: str,
        username: str,
        admin_username: str,
    ) -> None:
        """Уведомление о разблокировке пользователя"""
        message = (
            f"✅ <b>Пользователь разблокирован</b>\n\n"
            f"ID: <code>{user_id}</code>\n"
            f"Email: <code>{email}</code>\n"
            f"Username: <code>{username}</code>\n"
            f"Администратор: <code>{admin_username}</code>"
        )
        
        for chat_id in self.admin_chat_ids:
            await self._send_message(chat_id, message)

    async def notify_role_changed(
        self,
        user_id: UUID,
        email: str,
        username: str,
        old_role: str,
        new_role: str,
        admin_username: str,
    ) -> None:
        """Уведомление об изменении роли пользователя"""
        message = (
            f"👤 <b>Изменение роли пользователя</b>\n\n"
            f"ID: <code>{user_id}</code>\n"
            f"Email: <code>{email}</code>\n"
            f"Username: <code>{username}</code>\n"
            f"Старая роль: <code>{old_role}</code>\n"
            f"Новая роль: <code>{new_role}</code>\n"
            f"Администратор: <code>{admin_username}</code>"
        )
        
        for chat_id in self.admin_chat_ids:
            await self._send_message(chat_id, message)

    async def notify_comment_reported(
        self,
        comment_id: UUID,
        book_title: str,
        comment_text: str,
        reporter_username: str,
        reason: str,
    ) -> None:
        """Уведомление о жалобе на комментарий"""
        message = (
            f"⚠️ <b>Жалоба на комментарий</b>\n\n"
            f"ID комментария: <code>{comment_id}</code>\n"
            f"Книга: <i>{book_title}</i>\n"
            f"Текст комментария: <i>{comment_text[:200]}...</i>\n"
            f"Причина: {reason}\n"
            f"Отправитель жалобы: <code>{reporter_username}</code>"
        )
        
        for chat_id in self.admin_chat_ids:
            await self._send_message(chat_id, message)

    async def notify_comment_moderated(
        self,
        comment_id: UUID,
        book_title: str,
        comment_text: str,
        moderator_username: str,
        reason: str,
    ) -> None:
        """Уведомление о модерации комментария"""
        message = (
            f"🗑 <b>Комментарий отмодерирован</b>\n\n"
            f"ID комментария: <code>{comment_id}</code>\n"
            f"Книга: <i>{book_title}</i>\n"
            f"Текст комментария: <i>{comment_text[:200]}...</i>\n"
            f"Причина: {reason}\n"
            f"Модератор: <code>{moderator_username}</code>"
        )
        
        for chat_id in self.admin_chat_ids:
            await self._send_message(chat_id, message)

    async def notify_error(
        self,
        error_type: str,
        error_message: str,
        traceback: Optional[str] = None,
    ) -> None:
        """Уведомление об ошибке в системе"""
        message = (
            f"❌ <b>Ошибка в системе</b>\n\n"
            f"Тип: <code>{error_type}</code>\n"
            f"Сообщение: <code>{error_message}</code>"
        )
        
        if traceback:
            message += f"\n\nTraceback:\n<pre>{traceback[:1000]}</pre>"
        
        for chat_id in self.admin_chat_ids:
            await self._send_message(chat_id, message) 