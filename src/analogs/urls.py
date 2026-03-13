from django.urls import path

from .views import search

app_name = "analogs"

urlpatterns = [
    path("", search, name="search"),
]