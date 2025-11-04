from django.test import TestCase

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'telegram_django_bot.settings')
django.setup()

from core.bot import setup_bot
bot = setup_bot()
print("✅ Тест пройден - бот создан!")
