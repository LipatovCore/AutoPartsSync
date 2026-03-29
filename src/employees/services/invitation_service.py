from dataclasses import dataclass
import hashlib
import secrets

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from employees.models import Employee, EmployeeInvitation
from employees.repositories.invitation_repository import EmployeeInvitationRepository


class EmployeeInvitationServiceError(Exception):
    pass


@dataclass(frozen=True)
class InvitationIssueResult:
    employee: Employee
    invitation: EmployeeInvitation
    raw_token: str
    created_employee: bool


class EmployeeInvitationService:
    def __init__(self, repository: EmployeeInvitationRepository | None = None):
        self.repository = repository or EmployeeInvitationRepository()

    def create_employee_invitation(
        self,
        *,
        email: str,
        issued_by: Employee,
    ) -> InvitationIssueResult:
        normalized_email = Employee.objects.normalize_email(email).strip()
        employee = self.repository.get_employee_by_email(normalized_email)
        created_employee = False

        if employee is None:
            employee = self.repository.create_employee(email=normalized_email)
            created_employee = True
        elif employee.status != Employee.Status.CREATED:
            raise EmployeeInvitationServiceError(
                "Приглашение можно перевыпускать только для сотрудников со статусом created."
            )

        return self._issue_invitation(
            employee=employee,
            issued_by=issued_by,
            created_employee=created_employee,
        )

    def reissue_employee_invitation(
        self,
        *,
        employee_id: int,
        issued_by: Employee,
    ) -> InvitationIssueResult:
        employee = self.repository.get_employee_by_id(employee_id)
        if employee is None:
            raise EmployeeInvitationServiceError("Сотрудник не найден.")

        if employee.status != Employee.Status.CREATED:
            raise EmployeeInvitationServiceError(
                "Перевыпуск доступен только для сотрудников со статусом created."
            )

        return self._issue_invitation(
            employee=employee,
            issued_by=issued_by,
            created_employee=False,
        )

    def _issue_invitation(
        self,
        *,
        employee: Employee,
        issued_by: Employee,
        created_employee: bool,
    ) -> InvitationIssueResult:
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        issued_at = timezone.now()
        expires_at = issued_at + settings.EMPLOYEE_INVITATION_TTL

        with transaction.atomic():
            self.repository.revoke_active_invitations(
                employee=employee,
                revoked_at=issued_at,
            )
            invitation = self.repository.create_invitation(
                employee=employee,
                issued_by=issued_by,
                token_hash=token_hash,
                expires_at=expires_at,
            )

        return InvitationIssueResult(
            employee=employee,
            invitation=invitation,
            raw_token=raw_token,
            created_employee=created_employee,
        )
