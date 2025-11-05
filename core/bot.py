import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from django.conf import settings
from .models import TelegramUser, Event
from asgiref.sync import sync_to_async
from datetime import datetime, timedelta
from .models import Event
from asgiref.sync import sync_to_async
import datetime
from .models import BotSettings
from telegram.ext import MessageHandler, filters


CHAT_ID = 123456789  # временный chat_id для тестирования

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start для регистрации пользователей в боте."""
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

    group_link = "https://t.me/ваша_ссылка_на_группу"
    await update.message.reply_text(f"💬 Присоединяйтесь к общему чату: {group_link}")


async def send_reminder(context: ContextTypes.DEFAULT_TYPE, event: Event, chat_id: int):
    """Отправляет напоминание о мероприятии в указанный чат."""
    reminder_text = f"⏰ Напоминание о мероприятии:\n\n"
    reminder_text += f"📋 Мероприятие: {event.protocol}\n"
    if event.description:
        reminder_text += f"📝 Описание: {event.description}\n"
    reminder_text += f"👤 Ответственный: {event.responsible_person}\n"
    reminder_text += f"📅 Дедлайн: {event.deadline.strftime('%d.%m.%Y %H:%M')}\n"
    await context.bot.send_message(chat_id=chat_id, text=reminder_text)


async def check_upcoming_deadlines(context: ContextTypes.DEFAULT_TYPE):
    """Проверяет мероприятия с приближающимися дедлайнами и планирует напоминания."""
    from datetime import datetime, timedelta
    from .models import Event, BotSettings
    from asgiref.sync import sync_to_async

    settings = BotSettings.load()

    three_days_later = datetime.now() + timedelta(days=3)
    get_overdue_events = sync_to_async(
        lambda: Event.objects.filter(deadline__lt=datetime.now(), under_control=True).all()
    )
    get_upcoming_events = sync_to_async(
        lambda: Event.objects.filter(
            deadline__lte=three_days_later,
            deadline__gte=datetime.now(),
            under_control=True
        ).all()
    )
    overdue_events = await get_overdue_events()
    upcoming_events = await get_upcoming_events()

    for event in overdue_events:
        overdue_text = f"🚨 ПРОСРОЧЕНО!\n\n"
        overdue_text += f"📋 Мероприятие: {event.protocol}\n"
        overdue_text += f"📅 Просроченный дедлайн: {event.deadline.strftime('%d.%m.%Y %H:%M')}\n"
        overdue_text += f"👤 Ответственный: {event.responsible_person}\n"
        await context.bot.send_message(chat_id=CHAT_ID, text=overdue_text)

    for event in upcoming_events:
        await send_reminder(context, event, CHAT_ID)


async def send_daily_reminders(context: ContextTypes.DEFAULT_TYPE):
    """Отправляет ежедневные напоминания о всех мероприятиях под контролем."""
    from .models import Event, BotSettings
    from asgiref.sync import sync_to_async

    get_controlled_events = sync_to_async(
        lambda: Event.objects.filter(under_control=True).all()
    )
    controlled_events = await get_controlled_events()

    for event in controlled_events:
        await send_reminder(context, event, CHAT_ID)


async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type == "private":
        await update.message.reply_text("🤖 Я только отправляю напоминания. Используйте /start для меню.")
        return

    # Если это группа/канал - разрешаем все сообщения
    # Ничего не делаем - сообщения проходят свободно
    pass


def setup_bot() -> Application:
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).concurrent_updates(True).build()

    application.add_handler(CommandHandler("start", start))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_group_message))

    bot_settings = BotSettings.load()
    check_time = bot_settings.daily_check_time

    job_queue = application.job_queue

    if job_queue:
        job_queue.run_daily(check_upcoming_deadlines, time=check_time)
        job_queue.run_daily(send_daily_reminders, time=check_time)  # ← ДОБАВЛЯЕМ ЗДЕСЬ
    else:
        print("⚠️ Job queue недоступен - периодические проверки отключены")

    return application
