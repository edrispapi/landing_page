from django.contrib import admin

from .models import Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("phone_number", "status", "created_at", "processed_at")
    list_filter = ("status", "created_at")
    search_fields = ("phone_number",)
    ordering = ("-created_at",)
