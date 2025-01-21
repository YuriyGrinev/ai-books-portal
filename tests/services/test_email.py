from typing import AsyncGenerator

import pytest
from fastapi_mail import ConnectionConfig, FastMail
from pydantic import EmailStr

from books_portal.infrastructure.config.settings import settings
from books_portal.infrastructure.services.email import EmailService


@pytest.fixture
def email_config() -> ConnectionConfig:
    """Фикстура для создания конфигурации email"""
    return ConnectionConfig(
        MAIL_USERNAME=settings.MAIL_USERNAME,
        MAIL_PASSWORD=settings.MAIL_PASSWORD,
        MAIL_FROM=settings.MAIL_FROM,
        MAIL_PORT=settings.MAIL_PORT,
        MAIL_SERVER=settings.MAIL_SERVER,
        MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
        MAIL_STARTTLS=False,
        MAIL_SSL_TLS=True,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
        TEMPLATE_FOLDER=settings.EMAIL_TEMPLATES_DIR,
    )


@pytest.fixture
def email_service(email_config: ConnectionConfig) -> EmailService:
    """Фикстура для создания сервиса отправки email"""
    return EmailService(FastMail(email_config))


@pytest.fixture
def test_email() -> EmailStr:
    """Фикстура с тестовым email"""
    return EmailStr("test@example.com")


async def test_send_registration_email(
    email_service: EmailService,
    test_email: EmailStr,
) -> None:
    """Тест отправки email при регистрации"""
    # В тестовом окружении письмо не отправляется реально
    await email_service.send_registration_email(
        email=test_email,
        username="test_user",
    )


async def test_send_password_reset_email(
    email_service: EmailService,
    test_email: EmailStr,
) -> None:
    """Тест отправки email для сброса пароля"""
    await email_service.send_password_reset_email(
        email=test_email,
        username="test_user",
        token="test_token",
    )


async def test_send_password_changed_email(
    email_service: EmailService,
    test_email: EmailStr,
) -> None:
    """Тест отправки email об изменении пароля"""
    await email_service.send_password_changed_email(
        email=test_email,
        username="test_user",
    )


async def test_send_account_blocked_email(
    email_service: EmailService,
    test_email: EmailStr,
) -> None:
    """Тест отправки email о блокировке аккаунта"""
    await email_service.send_account_blocked_email(
        email=test_email,
        username="test_user",
        reason="Нарушение правил",
    )


async def test_send_account_unblocked_email(
    email_service: EmailService,
    test_email: EmailStr,
) -> None:
    """Тест отправки email о разблокировке аккаунта"""
    await email_service.send_account_unblocked_email(
        email=test_email,
        username="test_user",
    )


async def test_send_role_changed_email(
    email_service: EmailService,
    test_email: EmailStr,
) -> None:
    """Тест отправки email об изменении роли"""
    await email_service.send_role_changed_email(
        email=test_email,
        username="test_user",
        new_role="editor",
    )


async def test_send_comment_notification_email(
    email_service: EmailService,
    test_email: EmailStr,
) -> None:
    """Тест отправки email о новом комментарии"""
    await email_service.send_comment_notification_email(
        email=test_email,
        username="test_user",
        book_title="Test Book",
        comment_text="Test comment",
    )


async def test_send_reply_notification_email(
    email_service: EmailService,
    test_email: EmailStr,
) -> None:
    """Тест отправки email об ответе на комментарий"""
    await email_service.send_reply_notification_email(
        email=test_email,
        username="test_user",
        book_title="Test Book",
        reply_text="Test reply",
    )


async def test_send_comment_moderated_email(
    email_service: EmailService,
    test_email: EmailStr,
) -> None:
    """Тест отправки email о модерации комментария"""
    await email_service.send_comment_moderated_email(
        email=test_email,
        username="test_user",
        book_title="Test Book",
        comment_text="Test comment",
        reason="Нарушение правил",
    ) 