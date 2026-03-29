from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from employees.forms import EmployeeAuthenticationForm, EmployeeInvitationIssueForm
from employees.repositories.invitation_repository import EmployeeInvitationRepository
from employees.services.invitation_service import (
    EmployeeInvitationService,
    EmployeeInvitationServiceError,
)


class EmployeeLoginView(LoginView):
    authentication_form = EmployeeAuthenticationForm


def _ensure_system_admin(request):
    if not request.user.is_authenticated:
        return redirect(f"{reverse('login')}?next={request.path}")

    if not request.user.is_superuser:
        raise PermissionDenied

    return None


def _build_invitation_url(request, raw_token: str) -> str:
    invitation_path = f"/employees/invitations/{raw_token}/set-password/"
    return request.build_absolute_uri(invitation_path)


def employee_list(request):
    access_response = _ensure_system_admin(request)
    if access_response is not None:
        return access_response

    repository = EmployeeInvitationRepository()
    invitation_form = EmployeeInvitationIssueForm()
    invitation_url = request.session.pop("employee_invitation_url", None)
    invitation_email = request.session.pop("employee_invitation_email", None)

    context = {
        "invitation_form": invitation_form,
        "employees": repository.list_employees_with_invitations(),
        "invitation_url": invitation_url,
        "invitation_email": invitation_email,
    }
    return render(request, "employees/employee_management.html", context)


@require_POST
def employee_create(request):
    access_response = _ensure_system_admin(request)
    if access_response is not None:
        return access_response

    form = EmployeeInvitationIssueForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Не удалось создать приглашение. Проверьте email.")
        return render(
            request,
            "employees/employee_management.html",
            {
                "invitation_form": form,
                "employees": EmployeeInvitationRepository().list_employees_with_invitations(),
                "invitation_url": None,
                "invitation_email": None,
            },
        )

    service = EmployeeInvitationService()

    try:
        result = service.create_employee_invitation(
            email=form.cleaned_data["email"],
            issued_by=request.user,
        )
    except EmployeeInvitationServiceError as error:
        messages.error(request, str(error))
        return redirect(reverse("employees:list"))

    request.session["employee_invitation_url"] = _build_invitation_url(
        request,
        result.raw_token,
    )
    request.session["employee_invitation_email"] = result.employee.email

    if result.created_employee:
        messages.success(request, "Сотрудник создан, приглашение выпущено.")
    else:
        messages.success(request, "Приглашение перевыпущено.")

    return redirect(reverse("employees:list"))


@require_POST
def employee_reissue_invitation(request, employee_id: int):
    access_response = _ensure_system_admin(request)
    if access_response is not None:
        return access_response

    service = EmployeeInvitationService()

    try:
        result = service.reissue_employee_invitation(
            employee_id=employee_id,
            issued_by=request.user,
        )
    except EmployeeInvitationServiceError as error:
        messages.error(request, str(error))
        return redirect(reverse("employees:list"))

    request.session["employee_invitation_url"] = _build_invitation_url(
        request,
        result.raw_token,
    )
    request.session["employee_invitation_email"] = result.employee.email
    messages.success(request, "Приглашение перевыпущено.")
    return redirect(reverse("employees:list"))
