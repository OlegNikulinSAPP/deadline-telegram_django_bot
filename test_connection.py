import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'telegram_django_bot.settings')
django.setup()

import requests
from django.conf import settings

# Проверка интернета
try:
    response = requests.get('https://api.telegram.org', timeout=10)
    print(f"✅ Подключение к Telegram API: {response.status_code}")
except Exception as e:
    print(f"❌ Ошибка подключения: {e}")

# Проверка токена
if settings.TELEGRAM_BOT_TOKEN:
    print(f"✅ Токен загружен: {settings.TELEGRAM_BOT_TOKEN[:10]}...")
else:
    print("❌ Токен не загружен")