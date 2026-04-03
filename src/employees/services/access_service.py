from django.db import transaction

from employees.models import Employee, EmployeeAccessAuditEvent
from employees.repositories.invitation_repository import EmployeeInvitationRepository
from employees.services.audit_service import EmployeeAccessAuditService
from employees.services.session_service import EmployeeSessionService


class EmployeeAccessServiceError(Exception):
    pass


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
