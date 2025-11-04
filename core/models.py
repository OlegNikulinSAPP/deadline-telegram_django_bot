from django.db import models


class Event(models.Model):
    protocol = models.CharField(verbose_name="Мероприятие (Протокол)")
    description = models.TextField(verbose_name="Описание", blank=True)
    responsible_person = models.CharField(verbose_name="Ответственный", max_length=255)
    deadline = models.DateTimeField(verbose_name="Дедлайн")

    def __str__(self):
        return self.protocol
