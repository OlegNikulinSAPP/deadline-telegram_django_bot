import os
import django
import asyncio

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'telegram_django_bot.settings')
django.setup()

from core.bot import check_upcoming_deadlines
from telegram.ext import ContextTypes
from telegram import Bot
from django.conf import settings

class MockContext:
    def __init__(self):
        self.bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

print("🧪 Тестируем отправку напоминаний...")

# Создаем настоящий бот для контекста
context = MockContext()

# Запускаем проверку
asyncio.run(check_upcoming_deadlines(context))

print("✅ Тест завершен")