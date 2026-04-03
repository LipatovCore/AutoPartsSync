import hashlib

from employees.models import Employee, EmployeeAccessAuditEvent, EmployeeInvitation


class EmployeeAccessAuditService:
    def record_event(
        self,
        *,
        event_type: str,
        employee: Employee | None = None,
        actor: Employee | None = None,
        invitation: EmployeeInvitation | None = None,
        ip_address: str | None = None,
        metadata: dict | None = None,
    ) -> EmployeeAccessAuditEvent:
        cleaned_metadata = {
            key: value
            for key, value in (metadata or {}).items()
            if value is not None
        }

        return EmployeeAccessAuditEvent.objects.create(
            event_type=event_type,
            employee=employee,
            actor=actor,
            invitation=invitation,
            ip_address=ip_address or None,
            metadata=cleaned_metadata,
        )

    def record_activation_failed(
        self,
        *,
        raw_token: str,
        ip_address: str | None = None,
        reason: str | None = None,
    ) -> EmployeeAccessAuditEvent:
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        return self.record_event(
            event_type=EmployeeAccessAuditEvent.EventType.ACTIVATION_FAILED,
            ip_address=ip_address,
            metadata={
                "token_hash": token_hash,
                "reason": reason,
            },
        )
