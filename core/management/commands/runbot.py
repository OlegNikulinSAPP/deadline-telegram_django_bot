from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Django команда для запуска Telegram бота."""
    help = 'Запускает Telegram бота для напоминаний'

    def handle(self, *args, **options):
        from core.bot import setup_bot
        application = setup_bot()

        self.stdout.write("🤖 Запуск Telegram бота...")
        application.run_polling()
