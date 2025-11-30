import logging
import asyncio
import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from django.conf import settings
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

logger = logging.getLogger(__name__)

# Временный chat_id канала - ЗАМЕНИТЕ НА ВАШ РЕАЛЬНЫЙ CHAT_ID
CHAT_ID = -1003146050982  # ID канала "⏰ Дедлайны РИНПО"

# Глобальная переменная для планировщика
scheduler = None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start для регистрации пользователей в боте."""
    from .models import TelegramUser
    from asgiref.sync import sync_to_async

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

    # Отправляем ссылку на канал
    group_link = "https://t.me/deadline_reminders"
    await update.message.reply_text(
        f"💬 Присоединяйтесь к каналу с напоминаниями: {group_link}",
        disable_web_page_preview=True
    )


async def send_reminder_improved(context: ContextTypes.DEFAULT_TYPE, event, chat_id: int):
    """Улучшенная отправка напоминания о мероприятии"""
    from .models import Event

    # Упрощенный и более надежный формат текста
    from django.utils import timezone

    current_date = timezone.now().strftime('%d.%m.%Y')

    reminder_text = (
        f"🕐 <b>{current_date}</b>\n\n"
        f"⏰ <b>Напоминание!</b> ⏰\n\n"
        f"📋 <b>Мероприятие:</b> {event.protocol}\n\n"
    )
    if event.description:
        desc = event.description[:200] + "..." if len(event.description) > 200 else event.description
        reminder_text += f"📝 <b>Описание:</b> {desc}\n\n"
    reminder_text += (
        f"👤 <b>Ответственный:</b> {event.responsible_person}\n\n"
        f"📅 <b>Срок:</b> {event.deadline.strftime('%d.%m.%Y %H:%M')}"
    )

    try:
        await asyncio.wait_for(
            context.bot.send_message(
                chat_id=chat_id,
                text=reminder_text,
                parse_mode='HTML'
            ),
            timeout=30.0
        )
    except asyncio.TimeoutError:
        print(f"❌ Таймаут отправки напоминания для {event.protocol}")
        raise
    except Exception as e:
        print(f"❌ Ошибка отправки напоминания для {event.protocol}: {e}")
        raise


async def send_all_reminders():
    """Отправляет все напоминания за один запуск с улучшенными повторными попытками"""
    from datetime import timedelta
    from .models import Event, BotSettings
    from asgiref.sync import sync_to_async
    from django.utils import timezone
    from telegram import Bot
    from telegram.error import TelegramError

    print("🎯 ЗАПУСК ВСЕХ НАПОМИНАНИЙ")

    try:
        # Получаем настройки
        settings_obj = await sync_to_async(BotSettings.objects.get)(id=1)

        # Создаем контекст для бота
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

        class MockContext:
            def __init__(self, bot):
                self.bot = bot

        context = MockContext(bot)

        # Находим мероприятия
        three_days_later = timezone.now() + timedelta(days=3)

        all_events = await sync_to_async(
            lambda: list(Event.objects.filter(
                under_control=True,
                deadline__lte=three_days_later
            ))
        )()

        print(f"🔍 Найдено мероприятий для напоминаний: {len(all_events)}")

        if not all_events:
            print("ℹ️ Нет мероприятий для напоминаний")
            return

        # Отправляем все напоминания с улучшенными повторными попытками
        successful_sent = 0
        failed_sent = 0
        failed_events = []

        for i, event in enumerate(all_events):
            max_retries = 5  # Увеличили до 5 попыток
            retry_delays = [5, 10, 15, 20, 30]  # Прогрессивная задержка
            last_error = None

            for attempt in range(max_retries):
                try:
                    days_until_deadline = (event.deadline - timezone.now()).days

                    if days_until_deadline < 0:
                        # ПРОСРОЧЕНО
                        if attempt == 0:
                            print(f"📨 Отправка напоминания о ПРОСРОЧЕННОМ: {event.protocol}")
                        else:
                            print(f"🔄 Повторная попытка {attempt + 1}/{max_retries}: {event.protocol}")

                        # Упрощаем текст для надежности
                        from django.utils import timezone

                        current_date = timezone.now().strftime('%d.%m.%Y')
                        days_overdue = (timezone.now() - event.deadline).days

                        overdue_text = (
                            f"🕐 <b>{current_date}</b>\n\n"
                            f"🚨 <b>ПРОСРОЧЕНО!</b> 🚨\n\n"
                            f"📋 <b>Мероприятие:</b> {event.protocol}\n\n"
                        )
                        if event.description:
                            desc = event.description[:200] + "..." if len(
                                event.description) > 200 else event.description
                            overdue_text += f"📝 <b>Описание:</b> {desc}\n\n"
                        overdue_text += (
                            f"👤 <b>Ответственный:</b> {event.responsible_person}\n\n"
                            f"📅 <b>Срок:</b> {event.deadline.strftime('%d.%m.%Y %H:%M')}\n\n"
                            f"⏳ <b>Просрочено дней:</b> {days_overdue}"
                        )

                        await asyncio.wait_for(
                            context.bot.send_message(
                                chat_id=CHAT_ID,
                                text=overdue_text,
                                parse_mode='HTML'
                            ),
                            timeout=30.0
                        )
                        successful_sent += 1
                        print(f"✅ Успешно отправлено: {event.protocol}")
                        break  # Выходим из цикла попыток при успехе

                    else:
                        # СРОЧНО (до 3 дней)
                        if attempt == 0:
                            print(f"📨 Отправка напоминания: {event.protocol} (осталось {days_until_deadline} дней)")
                        else:
                            print(f"🔄 Повторная попытка {attempt + 1}/{max_retries}: {event.protocol}")

                        await asyncio.wait_for(
                            send_reminder_improved(context, event, CHAT_ID),
                            timeout=30.0
                        )
                        successful_sent += 1
                        print(f"✅ Успешно отправлено: {event.protocol}")
                        break  # Выходим из цикла попыток при успехе

                except asyncio.TimeoutError:
                    last_error = "Таймаут"
                    if attempt < max_retries - 1:
                        delay = retry_delays[attempt]
                        print(f"⏳ Таймаут, повтор через {delay} сек... (попытка {attempt + 1}/{max_retries})")
                        await asyncio.sleep(delay)
                    else:
                        print(f"❌ Не удалось отправить после {max_retries} попыток: {event.protocol} - {last_error}")
                        failed_sent += 1
                        failed_events.append(f"{event.protocol} - {last_error}")

                except TelegramError as e:
                    last_error = f"Telegram Error: {e}"
                    if attempt < max_retries - 1:
                        delay = retry_delays[attempt]
                        print(f"⚠️ Ошибка Telegram, повтор через {delay} сек... (попытка {attempt + 1}/{max_retries})")
                        await asyncio.sleep(delay)
                    else:
                        print(f"❌ Не удалось отправить после {max_retries} попыток: {event.protocol} - {last_error}")
                        failed_sent += 1
                        failed_events.append(f"{event.protocol} - {last_error}")

                except Exception as e:
                    last_error = f"Ошибка: {str(e)}"
                    if attempt < max_retries - 1:
                        delay = retry_delays[attempt]
                        print(f"⚠️ Ошибка: {e}, повтор через {delay} сек... (попытка {attempt + 1}/{max_retries})")
                        await asyncio.sleep(delay)
                    else:
                        print(f"❌ Не удалось отправить после {max_retries} попыток: {event.protocol} - {last_error}")
                        failed_sent += 1
                        failed_events.append(f"{event.protocol} - {last_error}")

            # Задержка между разными мероприятиями
            if i < len(all_events) - 1:
                delay_minutes = settings_obj.reminder_interval
                print(f"⏳ Ждем {delay_minutes} минут до следующего мероприятия...")
                await asyncio.sleep(delay_minutes * 60)

        # Детальный отчет
        print(f"\n📊 ИТОГОВЫЙ ОТЧЕТ:")
        print(f"✅ Успешно отправлено: {successful_sent}")
        print(f"❌ Не удалось отправить: {failed_sent}")

        if failed_events:
            print(f"📋 Проблемные напоминания:")
            for failed in failed_events:
                print(f"   • {failed}")

    except Exception as e:
        print(f"❌ Критическая ошибка при отправке напоминаний: {e}")


async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает сообщения от пользователей с проверкой типа чата."""
    if update.message.chat.type == "private":
        await update.message.reply_text("🤖 Я только отправляю напоминания. Используйте /start для меню.")
        return
    # Если это группа/канал - разрешаем все сообщения
    pass


async def setup_scheduler():
    """Настройка и запуск планировщика"""
    global scheduler

    from .models import BotSettings
    from asgiref.sync import sync_to_async

    try:
        # Создаем планировщик
        scheduler = AsyncIOScheduler()

        # Получаем время из БД
        settings_obj = await sync_to_async(BotSettings.objects.get)(id=1)
        check_time = settings_obj.daily_check_time
        hour = check_time.hour
        minute = check_time.minute

        # Добавляем задачу
        scheduler.add_job(
            send_all_reminders,
            trigger=CronTrigger(hour=hour, minute=minute, timezone='Europe/Moscow'),
            id='daily_reminders',
            replace_existing=True
        )

        # Запускаем планировщик
        scheduler.start()

        print(f"✅ Планировщик настроен на время: {hour:02d}:{minute:02d} (МСК)")
        print("✅ APScheduler запущен и работает")

        # Проверяем следующее время запуска
        job = scheduler.get_job('daily_reminders')
        if job and job.next_run_time:
            moscow_tz = pytz.timezone('Europe/Moscow')
            next_run = job.next_run_time.astimezone(moscow_tz)
            print(f"⏰ Следующий запуск: {next_run.strftime('%d.%m.%Y %H:%M')}")

    except Exception as e:
        print(f"❌ Ошибка настройки планировщика: {e}")
        # Перезапускаем через 30 секунд при ошибке
        await asyncio.sleep(30)
        await setup_scheduler()


async def check_scheduler_settings():
    """Упрощенная проверка и обновление настроек планировщика"""
    from .models import BotSettings
    from asgiref.sync import sync_to_async

    print("🔧 Запущена проверка настроек планировщика")

    last_hour = None
    last_minute = None

    while True:
        try:
            if scheduler:
                # Получаем текущие настройки
                settings_obj = await sync_to_async(BotSettings.objects.get)(id=1)
                new_hour = settings_obj.daily_check_time.hour
                new_minute = settings_obj.daily_check_time.minute

                print(f"🔍 Проверка настроек: время из БД = {new_hour:02d}:{new_minute:02d}")

                # Если настройки изменились или это первая проверка
                if last_hour != new_hour or last_minute != new_minute:
                    print(f"🔄 Обновление расписания: {new_hour:02d}:{new_minute:02d}")

                    # Всегда обновляем задачу
                    scheduler.add_job(
                        send_all_reminders,
                        trigger=CronTrigger(
                            hour=new_hour,
                            minute=new_minute,
                            timezone='Europe/Moscow'
                        ),
                        id='daily_reminders',
                        replace_existing=True
                    )

                    # Проверяем следующее время запуска
                    job = scheduler.get_job('daily_reminders')
                    if job and job.next_run_time:
                        moscow_tz = pytz.timezone('Europe/Moscow')
                        next_run = job.next_run_time.astimezone(moscow_tz)
                        print(f"✅ Расписание обновлено! Следующий запуск: {next_run.strftime('%d.%m.%Y %H:%M')}")
                    else:
                        print("✅ Расписание обновлено!")

                    last_hour = new_hour
                    last_minute = new_minute
                else:
                    print("✅ Настройки не изменились")
            else:
                print("❌ Планировщик не инициализирован")
                await setup_scheduler()

            await asyncio.sleep(60)  # Проверяем каждую минуту

        except Exception as e:
            print(f"❌ Ошибка проверки настроек планировщика: {e}")
            await asyncio.sleep(60)


def start_background_scheduler():
    """Запускает асинхронный планировщик в отдельном потоке"""

    async def main():
        await setup_scheduler()
        await check_scheduler_settings()

    def run_async():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(main())
        except Exception as e:
            print(f"❌ Критическая ошибка планировщика: {e}")
        finally:
            loop.close()

    scheduler_thread = threading.Thread(target=run_async, daemon=True)
    scheduler_thread.start()
    print("✅ Фоновый планировщик запущен")


def setup_bot() -> Application:
    """Создает и настраивает экземпляр Telegram бота с обработчиками."""
    application = (
        Application.builder()
        .token(settings.TELEGRAM_BOT_TOKEN)
        .concurrent_updates(True)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_group_message))

    # Запускаем фоновый планировщик
    start_background_scheduler()

    return application


def stop_scheduler():
    """Останавливает планировщик (для использования при остановке приложения)"""
    global scheduler
    if scheduler:
        scheduler.shutdown()
        print("✅ Планировщик остановлен")