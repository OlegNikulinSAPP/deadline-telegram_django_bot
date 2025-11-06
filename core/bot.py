import logging
import asyncio
import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from django.conf import settings
from django.utils import timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger


logger = logging.getLogger(__name__)

CHAT_ID = -1003146050982  # ID канала "⏰ Дедлайны РИНПО"

scheduler = None  # 🪑 "Здесь будет планировщик, но его пока нет"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start для регистрации пользователей в боте."""
    from .models import TelegramUser
    from asgiref.sync import sync_to_async

    user = update.message.from_user

    logger.info(
        f"""
        📋 ПАСПОРТ ПОЛЬЗОВАТЕЛЯ:
        🔢 ID: {user.id}
        📛 Имя: {user.first_name}
        📛 Фамилия: {user.last_name or 'не указана'}
        @ Юзернейм: @{user.username or 'не указан'}
        🤖 Бот: {'Да' if user.is_bot else 'Нет'}
        🈷️ Язык: {user.language_code or 'не указан'}
        """
    )

    get_or_create_user = sync_to_async(TelegramUser.objects.get_or_create)

    telegram_user, created = await get_or_create_user(
        user_id=user.id,
        default={
            'username': user.username or '',
            'first_name': user.first_name or '',
            'last_name': user.last_name,
        }
    )

    if created:
        logger.info(f'Зарегистрирован новый пользователь {user.id} - {user.first_name}')
    else:
        logger.info(f'Пользователь уже существует {user.id} - {user.first_name}')

    welcome_text = '👋 Добро пожаловать! Этот бот регистрирует Вас в приватном канале ООО РИНПО'
    await update.message.reply_text(welcome_text)

    group_link = "https://t.me/deadline_reminders"
    await update.message.reply_text(f'💬 Подключайтесь к приватному каналу:\n {group_link}')
