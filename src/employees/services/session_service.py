from django.contrib.auth import SESSION_KEY
from django.contrib.sessions.models import Session

from employees.models import Employee


class EmployeeSessionService:
    def terminate_employee_sessions(self, *, employee: Employee) -> int:
        employee_id = str(employee.pk)
        sessions_to_delete: list[str] = []

        for session in Session.objects.all():
            session_data = session.get_decoded()
            if session_data.get(SESSION_KEY) == employee_id:
                sessions_to_delete.append(session.session_key)

        if not sessions_to_delete:
            return 0

        deleted_count, _ = Session.objects.filter(
            session_key__in=sessions_to_delete
        ).delete()
        return deleted_count
