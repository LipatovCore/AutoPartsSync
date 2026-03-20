from django.contrib import admin

from .models import Car, Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "created_at")
    search_fields = ("name", "phone")


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ("brand", "model", "license_plate", "client", "created_at")
    search_fields = ("brand", "model", "license_plate", "vin", "client__name")