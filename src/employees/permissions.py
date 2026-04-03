from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from employees.models import Employee

ADMIN_GROUP_NAME = "admin"
USER_GROUP_NAME = "user"

MANAGE_EMPLOYEE_ACCESS = "employees.manage_employee_access"
VIEW_EMPLOYEE_ACCESS_AUDIT = "employees.view_employee_access_audit"

DEFAULT_GROUP_PERMISSIONS = {
    ADMIN_GROUP_NAME: (
        MANAGE_EMPLOYEE_ACCESS,
        VIEW_EMPLOYEE_ACCESS_AUDIT,
    ),
    USER_GROUP_NAME: (),
}


def has_employee_access_management(user) -> bool:
    return user.is_authenticated and user.has_perm(MANAGE_EMPLOYEE_ACCESS)


def has_employee_access_audit_view(user) -> bool:
    return user.is_authenticated and user.has_perm(VIEW_EMPLOYEE_ACCESS_AUDIT)


def ensure_default_employee_groups(**kwargs):
    content_type = ContentType.objects.get_for_model(Employee)
    permissions_by_codename = {
        permission.codename: permission
        for permission in Permission.objects.filter(
            content_type=content_type,
            codename__in={
                permission_name.split(".", 1)[1]
                for permissions in DEFAULT_GROUP_PERMISSIONS.values()
                for permission_name in permissions
            },
        )
    }

    for group_name, permission_names in DEFAULT_GROUP_PERMISSIONS.items():
        group, _ = Group.objects.get_or_create(name=group_name)
        group.permissions.set(
            [
                permissions_by_codename[permission_name.split(".", 1)[1]]
                for permission_name in permission_names
            ]
        )
