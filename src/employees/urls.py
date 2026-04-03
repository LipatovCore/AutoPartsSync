from django.urls import path

from employees.views import (
    employee_create,
    employee_deactivate,
    employee_list,
    employee_reissue_invitation,
    employee_reset_access,
    employee_set_password,
)

app_name = "employees"

urlpatterns = [
    path("", employee_list, name="list"),
    path("create/", employee_create, name="create"),
    path(
        "invitations/<str:token>/set-password/",
        employee_set_password,
        name="set-password",
    ),
    path(
        "<int:employee_id>/reissue-invitation/",
        employee_reissue_invitation,
        name="reissue-invitation",
    ),
    path(
        "<int:employee_id>/reset-access/",
        employee_reset_access,
        name="reset-access",
    ),
    path("<int:employee_id>/deactivate/", employee_deactivate, name="deactivate"),
]
