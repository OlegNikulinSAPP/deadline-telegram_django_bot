from django.contrib import admin
from django.urls import path, include

from . import views
from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('protocol', 'description', 'responsible_person', 'deadline')


# class CustomAdminSite(admin.AdminSite):
#     def get_urls(self):
#         urls = super().get_urls()
#         custom_urls = [
#             path('tools/upload-excel/', self.admin_view(views.upload_excel), name='upload_excel'),
#             ]
#         return urls + custom_urls
#
#
# custom_admin_site = CustomAdminSite(name='custom_admin')
# custom_admin_site.register(Event, EventAdmin)
