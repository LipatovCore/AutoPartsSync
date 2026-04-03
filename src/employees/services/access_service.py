from dataclasses import dataclass
import hashlib
import secrets

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from employees.models import Employee, EmployeeAccessAuditEvent, EmployeeInvitation
from employees.repositories.invitation_repository import EmployeeInvitationRepository
from employees.services.audit_service import EmployeeAccessAuditService
from employees.services.session_service import EmployeeSessionService


class EmployeeAccessServiceError(Exception):
    pass


@dataclass(frozen=True)
class EmployeeAccessResetResult:
    employee: Employee
    invitation: EmployeeInvitation
    raw_token: str
    terminated_sessions_count: int


class EmployeeAccessService:
    def __init__(
        self,
        repository: EmployeeInvitationRepository | None = None,
        audit_service: EmployeeAccessAuditService | None = None,
        session_service: EmployeeSessionService | None = None,
    ):
        self.repository = repository or EmployeeInvitationRepository()
        self.audit_service = audit_service or EmployeeAccessAuditService()
        self.session_service = session_service or EmployeeSessionService()

    def deactivate_employee(
        self,
        *,
        employee_id: int,
        actor: Employee,
        ip_address: str | None = None,
    ) -> Employee:
        employee = self.repository.get_employee_by_id(employee_id)
        if employee is None:
            raise EmployeeAccessServiceError("Сотрудник не найден.")

        if employee.pk == actor.pk:
            raise EmployeeAccessServiceError(
                "Нельзя деактивировать собственную учетную запись."
            )

        if employee.status == Employee.Status.DEACTIVATED:
            raise EmployeeAccessServiceError("Сотрудник уже деактивирован.")

        with transaction.atomic():
            self.repository.deactivate_employee(employee=employee)
            self.session_service.terminate_employee_sessions(employee=employee)
            self.audit_service.record_event(
                event_type=EmployeeAccessAuditEvent.EventType.EMPLOYEE_DEACTIVATED,
                employee=employee,
                actor=actor,
                ip_address=ip_address,
            )

        return employee

    def reset_employee_access(
        self,
        *,
        employee_id: int,
        actor: Employee,
        ip_address: str | None = None,
    ) -> EmployeeAccessResetResult:
        employee = self.repository.get_employee_by_id(employee_id)
        if employee is None:
            raise EmployeeAccessServiceError("Сотрудник не найден.")

        if employee.pk == actor.pk:
            raise EmployeeAccessServiceError(
                "Нельзя сбрасывать доступ для собственной учетной записи."
            )

        if employee.status != Employee.Status.ACTIVE:
            raise EmployeeAccessServiceError(
                "Сброс доступа доступен только для активных сотрудников."
            )

        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        issued_at = timezone.now()
        expires_at = issued_at + settings.EMPLOYEE_INVITATION_TTL
        revoked_invitations = self.repository.list_active_invitations(employee=employee)

        with transaction.atomic():
            self.repository.reset_employee_access(employee=employee)
            self.repository.revoke_active_invitations(
                employee=employee,
                revoked_at=issued_at,
            )
            invitation = self.repository.create_invitation(
                employee=employee,
                issued_by=actor,
                token_hash=token_hash,
                expires_at=expires_at,
            )
            terminated_sessions_count = self.session_service.terminate_employee_sessions(
                employee=employee
            )
            for revoked_invitation in revoked_invitations:
                self.audit_service.record_event(
                    event_type=EmployeeAccessAuditEvent.EventType.INVITATION_REVOKED,
                    employee=employee,
                    actor=actor,
                    invitation=revoked_invitation,
                    ip_address=ip_address,
                    metadata={"reason": "access_reset"},
                )
            self.audit_service.record_event(
                event_type=EmployeeAccessAuditEvent.EventType.ACCESS_RESET,
                employee=employee,
                actor=actor,
                invitation=invitation,
                ip_address=ip_address,
                metadata={
                    "previous_status": Employee.Status.ACTIVE,
                    "new_status": Employee.Status.CREATED,
                    "terminated_sessions_count": terminated_sessions_count,
                },
            )
            self.audit_service.record_event(
                event_type=EmployeeAccessAuditEvent.EventType.INVITATION_ISSUED,
                employee=employee,
                actor=actor,
                invitation=invitation,
                ip_address=ip_address,
                metadata={
                    "created_employee": False,
                    "expires_at": expires_at.isoformat(),
                    "reason": "access_reset",
                },
            )

        return EmployeeAccessResetResult(
            employee=employee,
            invitation=invitation,
            raw_token=raw_token,
            terminated_sessions_count=terminated_sessions_count,
        )
