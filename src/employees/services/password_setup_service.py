from __future__ import annotations

import hashlib

from django.db import transaction
from django.utils import timezone

from employees.models import Employee, EmployeeAccessAuditEvent, EmployeeInvitation
from employees.repositories.invitation_repository import EmployeeInvitationRepository
from employees.services.audit_service import EmployeeAccessAuditService
from employees.services.session_service import EmployeeSessionService


class EmployeePasswordSetupServiceError(Exception):
    pass


class EmployeePasswordSetupService:
    INVALID_LINK_MESSAGE = (
        "Ссылка недействительна. Обратитесь к администратору, чтобы получить новую ссылку."
    )

    def __init__(
        self,
        repository: EmployeeInvitationRepository | None = None,
        audit_service: EmployeeAccessAuditService | None = None,
        session_service: EmployeeSessionService | None = None,
    ):
        self.repository = repository or EmployeeInvitationRepository()
        self.audit_service = audit_service or EmployeeAccessAuditService()
        self.session_service = session_service or EmployeeSessionService()

    def get_invitation_for_token(self, *, raw_token: str) -> EmployeeInvitation:
        invitation = self._get_valid_invitation(raw_token=raw_token)
        return invitation

    def activate_employee_with_password(
        self,
        *,
        raw_token: str,
        password: str,
        ip_address: str | None = None,
    ) -> EmployeeInvitation:
        invitation = self._get_valid_invitation(raw_token=raw_token)
        employee = invitation.employee
        used_at = timezone.now()

        with transaction.atomic():
            employee.set_password(password)
            employee.save(update_fields=["password"])
            self.repository.activate_employee(employee=employee)
            self.repository.mark_invitation_used(invitation=invitation, used_at=used_at)
            self.session_service.terminate_employee_sessions(employee=employee)
            self.audit_service.record_event(
                event_type=EmployeeAccessAuditEvent.EventType.ACTIVATION_SUCCEEDED,
                employee=employee,
                invitation=invitation,
                ip_address=ip_address,
            )

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
