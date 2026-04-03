from django.apps import AppConfig
from django.db.models.signals import post_migrate


class EmployeesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "employees"

    def ready(self):
        from employees.permissions import ensure_default_employee_groups

        post_migrate.connect(
            ensure_default_employee_groups,
            sender=self,
            dispatch_uid="employees.ensure_default_employee_groups",
        )

