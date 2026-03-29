from django.db.models import Prefetch, QuerySet

from employees.models import Employee, EmployeeInvitation


class EmployeeInvitationRepository:
    def get_employee_by_email(self, email: str) -> Employee | None:
        return Employee.objects.filter(email=email).first()

    def get_employee_by_id(self, employee_id: int) -> Employee | None:
        return Employee.objects.filter(pk=employee_id).first()

    def create_employee(self, *, email: str) -> Employee:
        return Employee.objects.create_user(email=email, password=None)

    def revoke_active_invitations(self, *, employee: Employee, revoked_at) -> int:
        return (
            EmployeeInvitation.objects.filter(
                employee=employee,
                used_at__isnull=True,
                revoked_at__isnull=True,
            ).update(revoked_at=revoked_at)
        )

    def create_invitation(
        self,
        *,
        employee: Employee,
        issued_by: Employee,
        token_hash: str,
        expires_at,
    ) -> EmployeeInvitation:
        return EmployeeInvitation.objects.create(
            employee=employee,
            issued_by=issued_by,
            token_hash=token_hash,
            expires_at=expires_at,
        )

    def get_active_invitation_by_token_hash(self, token_hash: str) -> EmployeeInvitation | None:
        return (
            EmployeeInvitation.objects.select_related("employee")
            .filter(
                token_hash=token_hash,
                used_at__isnull=True,
                revoked_at__isnull=True,
            )
            .first()
        )

    def mark_invitation_used(self, *, invitation: EmployeeInvitation, used_at) -> EmployeeInvitation:
        invitation.used_at = used_at
        invitation.save(update_fields=["used_at", "updated_at"])
        return invitation

    def activate_employee(self, *, employee: Employee) -> Employee:
        employee.status = Employee.Status.ACTIVE
        employee.email_verified = True
        employee.save(update_fields=["status", "email_verified", "updated_at"])
        return employee

    def list_employees_with_invitations(self) -> QuerySet[Employee]:
        active_invitations = EmployeeInvitation.objects.filter(
            used_at__isnull=True,
            revoked_at__isnull=True,
        ).order_by("-created_at")

        return Employee.objects.order_by("email").prefetch_related(
            Prefetch(
                "invitations",
                queryset=active_invitations,
                to_attr="active_invitations",
            )
        )
