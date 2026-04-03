from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from employees.forms import (
    EmployeeAuthenticationForm,
    EmployeeInvitationIssueForm,
    EmployeePasswordSetupForm,
)
from employees.repositories.invitation_repository import EmployeeInvitationRepository
from employees.services.invitation_service import (
    EmployeeInvitationService,
    EmployeeInvitationServiceError,
)
from employees.services.audit_service import EmployeeAccessAuditService
from employees.services.password_setup_service import (
    EmployeePasswordSetupService,
    EmployeePasswordSetupServiceError,
)
from employees.services.security_service import EmployeeSecurityService


class EmployeeLoginView(LoginView):
    authentication_form = EmployeeAuthenticationForm
    security_service = EmployeeSecurityService()

    def post(self, request, *args, **kwargs):
        identifier = (request.POST.get("username") or "").strip().lower()
        rate_limit = self.security_service.check_rate_limit(
            scope="login",
            ip_address=_get_client_ip(request),
            identifier=identifier,
        )
        request._login_rate_limit_result = rate_limit

        if not rate_limit.allowed:
            form = self.get_form()
            form.add_error(
                None,
                (
                    "Превышен лимит попыток входа. "
                    f"Попробуйте снова через {rate_limit.retry_after_seconds} сек."
                ),
            )
            return self.form_invalid(form)

        return super().post(request, *args, **kwargs)

    def form_invalid(self, form):
        rate_limit = getattr(self.request, "_login_rate_limit_result", None)
        if (
            rate_limit is not None
            and rate_limit.allowed
            and rate_limit.attempts_left is not None
            and form.non_field_errors()
        ):
            if "__all__" in form.errors:
                del form.errors["__all__"]
            form.add_error(
                None,
                (
                    "Не удалось выполнить вход. Проверьте email и пароль. "
                    f"Осталось попыток: {rate_limit.attempts_left}."
                ),
            )

        return super().form_invalid(form)

    def form_valid(self, form):
        self.security_service.reset_rate_limit(
            scope="login",
            ip_address=_get_client_ip(self.request),
            identifier=form.cleaned_data["username"].strip().lower(),
        )
        return super().form_valid(form)


def _ensure_system_admin(request):
    if not request.user.is_authenticated:
        return redirect(f"{reverse('login')}?next={request.path}")

    if not request.user.is_superuser:
        raise PermissionDenied

    return None


def _build_invitation_url(request, raw_token: str) -> str:
    invitation_path = reverse("employees:set-password", args=[raw_token])
    return request.build_absolute_uri(invitation_path)


def _get_client_ip(request) -> str:
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


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
            ip_address=_get_client_ip(request),
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
    security_service = EmployeeSecurityService()
    rate_limit = security_service.check_rate_limit(
        scope="invitation_reissue",
        ip_address=_get_client_ip(request),
        identifier=str(employee_id),
    )
    if not rate_limit.allowed:
        messages.error(
            request,
            (
                "Превышен лимит попыток перевыпуска приглашения. "
                f"Попробуйте снова через {rate_limit.retry_after_seconds} сек."
            ),
        )
        return redirect(reverse("employees:list"))

    try:
        result = service.reissue_employee_invitation(
            employee_id=employee_id,
            issued_by=request.user,
            ip_address=_get_client_ip(request),
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


def employee_set_password(request, token: str):
    service = EmployeePasswordSetupService()
    audit_service = EmployeeAccessAuditService()
    security_service = EmployeeSecurityService()
    client_ip = _get_client_ip(request)
    rate_limit = security_service.check_rate_limit(
        scope="password_setup",
        ip_address=client_ip,
        identifier=token,
    )
    if not rate_limit.allowed:
        audit_service.record_activation_failed(
            raw_token=token,
            ip_address=client_ip,
            reason="rate_limited",
        )
        return render(
            request,
            "employees/set_password.html",
            {
                "form": None,
                "is_valid_link": False,
                "error_message": (
                    "Превышен лимит попыток установки пароля. "
                    f"Попробуйте снова через {rate_limit.retry_after_seconds} сек."
                ),
            },
        )

    try:
        invitation = service.get_invitation_for_token(raw_token=token)
    except EmployeePasswordSetupServiceError as error:
        audit_service.record_activation_failed(
            raw_token=token,
            ip_address=client_ip,
            reason="invalid_link",
        )
        return render(
            request,
            "employees/set_password.html",
            {
                "form": None,
                "is_valid_link": False,
                "error_message": str(error),
            },
        )

    form = EmployeePasswordSetupForm(user=invitation.employee, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        try:
            service.activate_employee_with_password(
                raw_token=token,
                password=form.cleaned_data["new_password1"],
                ip_address=client_ip,
            )
        except EmployeePasswordSetupServiceError as error:
            audit_service.record_activation_failed(
                raw_token=token,
                ip_address=client_ip,
                reason="invalid_link",
            )
            return render(
                request,
                "employees/set_password.html",
                {
                    "form": None,
                    "is_valid_link": False,
                    "error_message": str(error),
                },
            )

        messages.success(
            request,
            "Пароль установлен. Теперь войдите в систему по email и паролю.",
        )
        return redirect(reverse("login"))

    return render(
        request,
        "employees/set_password.html",
        {
            "form": form,
            "is_valid_link": True,
            "error_message": None,
        },
    )
