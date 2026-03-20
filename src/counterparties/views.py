from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Prefetch, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import CarForm, ClientForm
from .models import Car, Client


def _workspace_url(*, client_id=None, query="", dialog=None, car_editor=None):
    params = {}
    if query:
        params["q"] = query
    if client_id:
        params["client"] = client_id
    if dialog:
        params["dialog"] = dialog
    if car_editor:
        params["car_form"] = car_editor

    base_url = reverse("counterparties:client_list")
    return f"{base_url}?{urlencode(params)}" if params else base_url


def _select_client(clients, selected_client_id):
    if not clients:
        return None
    if selected_client_id is None:
        return clients[0]

    for client in clients:
        if client.pk == selected_client_id:
            return client

    return clients[0]


@login_required
def client_list(request):
    query = request.GET.get("q", "").strip()
    selected_client_id = request.GET.get("client")
    active_car_editor = request.GET.get("car_form", "").strip()

    try:
        selected_client_id = int(selected_client_id) if selected_client_id else None
    except (TypeError, ValueError):
        selected_client_id = None

    client_search = (
        Q(name__icontains=query)
        | Q(phone__icontains=query)
        | Q(cars__brand__icontains=query)
        | Q(cars__model__icontains=query)
        | Q(cars__license_plate__icontains=query)
        | Q(cars__vin__icontains=query)
    )
    car_search = (
        Q(brand__icontains=query)
        | Q(model__icontains=query)
        | Q(license_plate__icontains=query)
        | Q(vin__icontains=query)
    )

    clients_queryset = (
        Client.objects.annotate(total_cars=Count("cars", distinct=True))
        .prefetch_related(
            Prefetch(
                "cars",
                queryset=Car.objects.order_by("brand", "model", "license_plate"),
            )
        )
        .order_by("name")
    )

    if query:
        clients_queryset = clients_queryset.filter(client_search).distinct()

    clients = list(clients_queryset)
    selected_client = _select_client(clients, selected_client_id)
    selected_cars = list(selected_client.cars.all()) if selected_client else []
    matched_car_ids = set()
    active_car = None

    if query and selected_client:
        matched_car_ids = set(
            selected_client.cars.filter(car_search).values_list("id", flat=True)
        )

    if selected_client and active_car_editor and active_car_editor != "create":
        try:
            active_car_id = int(active_car_editor)
        except (TypeError, ValueError):
            active_car_id = None

        if active_car_id:
            active_car = next((car for car in selected_cars if car.pk == active_car_id), None)

    context = {
        "clients": clients,
        "selected_client": selected_client,
        "selected_cars": selected_cars,
        "matched_car_ids": matched_car_ids,
        "client_form": ClientForm(),
        "client_edit_form": ClientForm(instance=selected_client) if selected_client else None,
        "car_form": CarForm(),
        "query": query,
        "dialog": request.GET.get("dialog", "").strip(),
        "total_clients": len(clients),
        "active_car_editor": active_car_editor,
        "active_car": active_car,
    }
    return render(request, "counterparties/client_list.html", context)


@login_required
def client_detail(request, pk):
    get_object_or_404(Client, pk=pk)
    return redirect(_workspace_url(client_id=pk, query=request.GET.get("q", "").strip()))


@login_required
@require_POST
def client_create(request):
    form = ClientForm(request.POST)
    query = request.POST.get("query", "").strip()

    if form.is_valid():
        client = form.save()
        messages.success(request, "Контрагент создан.")
        car_editor = "create" if request.POST.get("add_car_after_save") else None
        return redirect(_workspace_url(client_id=client.pk, query=query, car_editor=car_editor))

    messages.error(request, "Ошибка при создании контрагента.")
    return redirect(_workspace_url(query=query, dialog="client-create"))


@login_required
@require_POST
def client_update(request, pk):
    client = get_object_or_404(Client, pk=pk)
    form = ClientForm(request.POST, instance=client)
    query = request.POST.get("query", "").strip()

    if form.is_valid():
        form.save()
        messages.success(request, "Контрагент обновлен.")
    else:
        messages.error(request, "Ошибка обновления контрагента.")

    return redirect(_workspace_url(client_id=client.pk, query=query))


@login_required
@require_POST
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)
    query = request.POST.get("query", "").strip()
    client.delete()
    messages.success(request, "Контрагент удален.")
    return redirect(_workspace_url(query=query))


@login_required
@require_POST
def car_create(request, client_pk):
    client = get_object_or_404(Client, pk=client_pk)
    form = CarForm(request.POST)
    query = request.POST.get("query", "").strip()

    if form.is_valid():
        car = form.save(commit=False)
        car.client = client
        car.save()
        messages.success(request, "Автомобиль добавлен.")
    else:
        messages.error(request, "Ошибка при добавлении автомобиля.")
        return redirect(_workspace_url(client_id=client.pk, query=query, car_editor="create"))

    return redirect(_workspace_url(client_id=client.pk, query=query))


@login_required
@require_POST
def car_update(request, pk):
    car = get_object_or_404(Car, pk=pk)
    form = CarForm(request.POST, instance=car)
    query = request.POST.get("query", "").strip()

    if form.is_valid():
        form.save()
        messages.success(request, "Автомобиль обновлен.")
    else:
        messages.error(request, "Не удалось обновить автомобиль.")
        return redirect(_workspace_url(client_id=car.client_id, query=query, car_editor=car.pk))

    return redirect(_workspace_url(client_id=car.client_id, query=query))


@login_required
@require_POST
def car_delete(request, pk):
    car = get_object_or_404(Car, pk=pk)
    client_id = car.client_id
    query = request.POST.get("query", "").strip()
    car.delete()
    messages.success(request, "Автомобиль удален.")
    return redirect(_workspace_url(client_id=client_id, query=query))
