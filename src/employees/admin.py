from django.contrib import admin

from employees.models import EmployeeAccessAuditEvent


@admin.register(EmployeeAccessAuditEvent)
class EmployeeAccessAuditEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "employee", "actor", "ip_address", "created_at")
    list_filter = ("event_type", "created_at")
    search_fields = ("employee__email", "actor__email", "ip_address")
    readonly_fields = (
        "event_type",
        "employee",
        "actor",
        "invitation",
        "ip_address",
        "metadata",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
