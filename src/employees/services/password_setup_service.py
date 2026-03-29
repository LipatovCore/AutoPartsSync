from __future__ import annotations

import hashlib

from django.contrib.auth import SESSION_KEY
from django.contrib.sessions.models import Session
from django.db import transaction
from django.utils import timezone

from employees.models import Employee, EmployeeInvitation
from employees.repositories.invitation_repository import EmployeeInvitationRepository


class EmployeePasswordSetupServiceError(Exception):
    pass


class EmployeePasswordSetupService:
    INVALID_LINK_MESSAGE = (
        "Ссылка недействительна. Обратитесь к администратору, чтобы получить новую ссылку."
    )

    def __init__(self, repository: EmployeeInvitationRepository | None = None):
        self.repository = repository or EmployeeInvitationRepository()

    def get_invitation_for_token(self, *, raw_token: str) -> EmployeeInvitation:
        invitation = self._get_valid_invitation(raw_token=raw_token)
        return invitation

    def activate_employee_with_password(
        self,
        *,
        raw_token: str,
        password: str,
    ) -> EmployeeInvitation:
        invitation = self._get_valid_invitation(raw_token=raw_token)
        employee = invitation.employee
        used_at = timezone.now()

        with transaction.atomic():
            employee.set_password(password)
            employee.save(update_fields=["password"])
            self.repository.activate_employee(employee=employee)
            self.repository.mark_invitation_used(invitation=invitation, used_at=used_at)
            self._terminate_employee_sessions(employee=employee)

        return invitation

    def _get_valid_invitation(self, *, raw_token: str) -> EmployeeInvitation:
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        invitation = self.repository.get_active_invitation_by_token_hash(token_hash)

        if invitation is None:
            raise EmployeePasswordSetupServiceError(self.INVALID_LINK_MESSAGE)

        if invitation.expires_at <= timezone.now():
            raise EmployeePasswordSetupServiceError(self.INVALID_LINK_MESSAGE)

        if invitation.employee.status != Employee.Status.CREATED:
            raise EmployeePasswordSetupServiceError(self.INVALID_LINK_MESSAGE)

        return invitation

    def _terminate_employee_sessions(self, *, employee: Employee) -> None:
        employee_id = str(employee.pk)
        sessions_to_delete: list[str] = []

        for session in Session.objects.all():
            session_data = session.get_decoded()
            if session_data.get(SESSION_KEY) == employee_id:
                sessions_to_delete.append(session.session_key)

        if sessions_to_delete:
            Session.objects.filter(session_key__in=sessions_to_delete).delete()
