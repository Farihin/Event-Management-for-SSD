from django.contrib import admin

from .models import Event, Registration


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "start_at", "capacity", "organizer")
    list_filter = ("status", "start_at")
    search_fields = ("title", "location")
    date_hierarchy = "start_at"


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("user__username", "event__title")
