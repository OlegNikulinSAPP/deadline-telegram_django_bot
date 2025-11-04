import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from django.conf import settings
from .models import TelegramUser
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    get_or_create_user = sync_to_async(TelegramUser.objects.get_or_create)

    telegram_user, created = await get_or_create_user(
        user_id=user.id,
        defaults={
            'username': user.username or '',
            'first_name': user.first_name or '',
            'last_name': user.last_name or '',
        }
    )

    if created:
        logger.info(f"Зарегистрирован новый пользователь: {user.id} - {user.first_name}")
    else:
        logger.info(f"Пользователь уже существует: {user.id} - {user.first_name}")

    welcome_text = "👋 Добро пожаловать! Этот бот отправляет напоминания о мероприятиях."
    await update.message.reply_text(welcome_text)


async def send_reminder(context: ContextTypes.DEFAULT_TYPE, event: Event, chat_id: int):


def setup_bot() -> Application:
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))

    return application
