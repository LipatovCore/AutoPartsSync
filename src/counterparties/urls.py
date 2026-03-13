from django.urls import path

from .views import (
    car_create,
    car_delete,
    car_update,
    client_create,
    client_delete,
    client_detail,
    client_list,
    client_update,
)

app_name = "counterparties"

urlpatterns = [
    path("clients/", client_list, name="client_list"),
    path("clients/create/", client_create, name="client_create"),
    path("clients/<int:pk>/", client_detail, name="client_detail"),
    path("clients/<int:pk>/update/", client_update, name="client_update"),
    path("clients/<int:pk>/delete/", client_delete, name="client_delete"),
    path("clients/<int:client_pk>/cars/create/", car_create, name="car_create"),
    path("cars/<int:pk>/update/", car_update, name="car_update"),
    path("cars/<int:pk>/delete/", car_delete, name="car_delete"),
]