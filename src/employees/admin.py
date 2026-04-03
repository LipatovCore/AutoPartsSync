from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from employees.models import Employee, EmployeeAccessAuditEvent, EmployeeInvitation
from employees.permissions import has_employee_access_audit_view


@admin.register(Employee)
class EmployeeAdmin(UserAdmin):
    ordering = ("email",)
    list_display = (
        "email",
        "status",
        "email_verified",
        "is_staff",
        "is_superuser",
        "last_login",
    )
    list_filter = ("status", "email_verified", "is_staff", "is_superuser", "groups")
    search_fields = ("email", "first_name", "last_name")
    readonly_fields = ("last_login", "date_joined", "created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        (
            "Access",
            {
                "fields": (
                    "status",
                    "email_verified",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "status",
                    "email_verified",
                    "is_staff",
                    "is_superuser",
                    "groups",
                ),
            },
        ),
    )


@admin.register(EmployeeInvitation)
class EmployeeInvitationAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "issued_by",
        "expires_at",
        "used_at",
        "revoked_at",
        "created_at",
    )
    list_filter = ("used_at", "revoked_at", "expires_at", "created_at")
    search_fields = ("employee__email", "issued_by__email", "token_hash")
    autocomplete_fields = ("employee", "issued_by")
    readonly_fields = ("created_at", "updated_at")


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

    def has_delete_permission(self, request, obj=None):
        return False

    def has_module_permission(self, request):
        return has_employee_access_audit_view(request.user)

    def has_view_permission(self, request, obj=None):
        return has_employee_access_audit_view(request.user)
