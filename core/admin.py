from django.contrib import admin

from .models import Event, TelegramUser, BotSettings


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('protocol', 'description', 'responsible_person', 'deadline', 'under_control')


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'username', 'first_name', 'last_name', 'can_send_message', 'registered_at')

@admin.register(BotSettings)
class BotSettingsAdmin(admin.ModelAdmin):
    list_display = ('reminder_interval', 'daily_check_time')
