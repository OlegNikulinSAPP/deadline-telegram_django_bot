from django.db import models


class Event(models.Model):
    """Модель для хранения информации о мероприятиях и дедлайнах."""
    protocol = models.CharField(verbose_name="Мероприятие (Протокол)")
    description = models.TextField(verbose_name="Описание", blank=True)
    responsible_person = models.CharField(verbose_name="Ответственный", max_length=255)
    deadline = models.DateTimeField(verbose_name="Дедлайн")

    def __str__(self):
        return self.protocol


class TelegramUser(models.Model):
    """Модель для хранения пользователей Telegram и их прав доступа."""
    user_id = models.BigIntegerField(unique=True, verbose_name="ID пользователя")
    username = models.CharField(max_length=255, blank=True, verbose_name="Username")
    first_name = models.CharField(max_length=255, blank=True, verbose_name="Имя")
    last_name = models.CharField(max_length=255, blank=True, verbose_name="Фамилия")
    can_send_message = models.BooleanField(default=False, verbose_name="Может отправлять сообщения")
    registered_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата регистрации")

    class Meta:
        verbose_name = "Пользователь Telegram"
        verbose_name_plural = "Пользователи Telegram"

    def __str__(self):
        return f'{self.first_name} {self.last_name} (@{self.username})' if self.username \
            else f'{self.first_name} {self.last_name}'
