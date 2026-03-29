from django.urls import path

from employees.views import employee_create, employee_list, employee_reissue_invitation

app_name = "employees"

urlpatterns = [
    path("", employee_list, name="list"),
    path("create/", employee_create, name="create"),
    path(
        "<int:employee_id>/reissue-invitation/",
        employee_reissue_invitation,
        name="reissue-invitation",
    ),
]
