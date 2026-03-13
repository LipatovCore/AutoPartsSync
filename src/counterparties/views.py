from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import CarForm, ClientForm
from .models import Car, Client


@login_required
def client_list(request):
    clients = Client.objects.order_by("name")

    context = {
        "clients": clients,
        "client_form": ClientForm(),
        "total_clients": clients.count(),
    }
    return render(request, "counterparties/client_list.html", context)


@login_required
def client_detail(request, pk):
    client = get_object_or_404(Client.objects.prefetch_related("cars"), pk=pk)

    context = {
        "client": client,
        "cars": client.cars.all(),
        "client_form": ClientForm(instance=client),
        "car_form": CarForm(),
    }
    return render(request, "counterparties/client_detail.html", context)


@require_POST
def client_create(request):
    form = ClientForm(request.POST)
    if form.is_valid():
        client = form.save()
        messages.success(request, "Контрагент создан.")
        return redirect("counterparties:client_detail", pk=client.pk)

    messages.error(request, "Ошибка при создании контрагента.")
    return redirect("counterparties:client_list")


@require_POST
def client_update(request, pk):
    client = get_object_or_404(Client, pk=pk)
    form = ClientForm(request.POST, instance=client)

    if form.is_valid():
        form.save()
        messages.success(request, "Контрагент обновлен.")
    else:
        messages.error(request, "Ошибка обновления контрагента.")

    return redirect("counterparties:client_detail", pk=client.pk)


@require_POST
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)
    client.delete()
    messages.success(request, "Контрагент удален.")
    return redirect("counterparties:client_list")


@require_POST
def car_create(request, client_pk):
    client = get_object_or_404(Client, pk=client_pk)
    form = CarForm(request.POST)

    if form.is_valid():
        car = form.save(commit=False)
        car.client = client
        car.save()
        messages.success(request, "Автомобиль добавлен.")
    else:
        messages.error(request, "Ошибка при добавлении автомобиля.")

    return redirect("counterparties:client_detail", pk=client.pk)


@require_POST
def car_update(request, pk):
    car = get_object_or_404(Car, pk=pk)
    form = CarForm(request.POST, instance=car)

    if form.is_valid():
        form.save()
        messages.success(request, "Автомобиль обновлен.")
    else:
        messages.error(request, "Не удалось обновить автомобиль.")

    return redirect("counterparties:client_detail", pk=car.client_id)


@require_POST
def car_delete(request, pk):
    car = get_object_or_404(Car, pk=pk)
    client_id = car.client_id
    car.delete()
    messages.success(request, "Автомобиль удален.")
    return redirect("counterparties:client_detail", pk=client_id)