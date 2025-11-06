from django.contrib import admin
from .models import Event, TelegramUser, BotSettings


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('protocol', 'description', 'responsible_person', 'deadline', 'under_control')
    list_filter = ('under_control', 'deadline')
    search_fields = ('protocol', 'description', 'responsible_person')
    date_hierarchy = 'deadline'


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'username', 'first_name', 'last_name', 'can_send_message', 'registered_at')
    list_filter = ('can_send_message', 'registered_at')
    search_fields = ('user_id', 'username', 'first_name', 'last_name')
    readonly_fields = ('registered_at',)


@admin.register(BotSettings)
class BotSettingsAdmin(admin.ModelAdmin):
    list_display = ('reminder_interval', 'daily_check_time')

    def has_add_permission(self, request):
        # Запрещаем создавать новые объекты, если уже есть один
        if BotSettings.objects.count() >= 1:
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        # Запрещаем удалять объект
        return False

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Логируем сохранение настроек
        print(f"⚙️ Настройки сохранены: время = {obj.daily_check_time}, интервал = {obj.reminder_interval} мин")
