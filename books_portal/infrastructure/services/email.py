from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr

from books_portal.domain.interfaces.email import EmailService as EmailServiceInterface
from books_portal.infrastructure.config.settings import settings


class EmailService(EmailServiceInterface):
    """Сервис отправки email"""

    def __init__(self, fastmail: FastMail) -> None:
        """Инициализация сервиса"""
        self.fastmail = fastmail

    async def _send_email(
        self,
        subject: str,
        recipients: List[EmailStr],
        template_name: str,
        template_data: Dict[str, Any],
    ) -> None:
        """Отправка email с использованием шаблона"""
        message = MessageSchema(
            subject=subject,
            recipients=recipients,
            template_body=template_data,
            subtype=MessageType.html,
        )
        
        await self.fastmail.send_message(
            message,
            template_name=template_name,
        )

    async def send_registration_email(
        self,
        email: EmailStr,
        username: str,
    ) -> None:
        """Отправка email при регистрации"""
        await self._send_email(
            subject="Добро пожаловать в Books Portal",
            recipients=[email],
            template_name="registration.html",
            template_data={
                "username": username,
                "site_name": settings.PROJECT_NAME,
                "site_url": settings.SITE_URL,
            },
        )

    async def send_password_reset_email(
        self,
        email: EmailStr,
        username: str,
        token: str,
    ) -> None:
        """Отправка email для сброса пароля"""
        reset_url = f"{settings.SITE_URL}/reset-password?token={token}"
        await self._send_email(
            subject="Сброс пароля",
            recipients=[email],
            template_name="password_reset.html",
            template_data={
                "username": username,
                "reset_url": reset_url,
                "site_name": settings.PROJECT_NAME,
                "expire_hours": 1,
            },
        )

    async def send_password_changed_email(
        self,
        email: EmailStr,
        username: str,
    ) -> None:
        """Отправка email об изменении пароля"""
        await self._send_email(
            subject="Пароль изменен",
            recipients=[email],
            template_name="password_changed.html",
            template_data={
                "username": username,
                "site_name": settings.PROJECT_NAME,
                "support_email": settings.SUPPORT_EMAIL,
            },
        )

    async def send_account_blocked_email(
        self,
        email: EmailStr,
        username: str,
        reason: str,
    ) -> None:
        """Отправка email о блокировке аккаунта"""
        await self._send_email(
            subject="Аккаунт заблокирован",
            recipients=[email],
            template_name="account_blocked.html",
            template_data={
                "username": username,
                "reason": reason,
                "site_name": settings.PROJECT_NAME,
                "support_email": settings.SUPPORT_EMAIL,
            },
        )

    async def send_account_unblocked_email(
        self,
        email: EmailStr,
        username: str,
    ) -> None:
        """Отправка email о разблокировке аккаунта"""
        await self._send_email(
            subject="Аккаунт разблокирован",
            recipients=[email],
            template_name="account_unblocked.html",
            template_data={
                "username": username,
                "site_name": settings.PROJECT_NAME,
                "site_url": settings.SITE_URL,
            },
        )

    async def send_role_changed_email(
        self,
        email: EmailStr,
        username: str,
        new_role: str,
    ) -> None:
        """Отправка email об изменении роли"""
        await self._send_email(
            subject="Изменение роли",
            recipients=[email],
            template_name="role_changed.html",
            template_data={
                "username": username,
                "new_role": new_role,
                "site_name": settings.PROJECT_NAME,
            },
        )

    async def send_comment_notification_email(
        self,
        email: EmailStr,
        username: str,
        book_title: str,
        comment_text: str,
    ) -> None:
        """Отправка email о новом комментарии"""
        await self._send_email(
            subject=f"Новый комментарий к книге {book_title}",
            recipients=[email],
            template_name="comment_notification.html",
            template_data={
                "username": username,
                "book_title": book_title,
                "comment_text": comment_text,
                "site_name": settings.PROJECT_NAME,
            },
        )

    async def send_reply_notification_email(
        self,
        email: EmailStr,
        username: str,
        book_title: str,
        reply_text: str,
    ) -> None:
        """Отправка email об ответе на комментарий"""
        await self._send_email(
            subject=f"Новый ответ на ваш комментарий к книге {book_title}",
            recipients=[email],
            template_name="reply_notification.html",
            template_data={
                "username": username,
                "book_title": book_title,
                "reply_text": reply_text,
                "site_name": settings.PROJECT_NAME,
            },
        )

    async def send_comment_moderated_email(
        self,
        email: EmailStr,
        username: str,
        book_title: str,
        comment_text: str,
        reason: str,
    ) -> None:
        """Отправка email о модерации комментария"""
        await self._send_email(
            subject=f"Ваш комментарий к книге {book_title} был отмодерирован",
            recipients=[email],
            template_name="comment_moderated.html",
            template_data={
                "username": username,
                "book_title": book_title,
                "comment_text": comment_text,
                "reason": reason,
                "site_name": settings.PROJECT_NAME,
                "support_email": settings.SUPPORT_EMAIL,
            },
        ) 