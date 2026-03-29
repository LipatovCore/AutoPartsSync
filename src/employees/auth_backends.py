from django.contrib.auth.backends import ModelBackend

from .models import Employee


class EmployeeAuthenticationBackend(ModelBackend):
    def user_can_authenticate(self, user):
        is_allowed = super().user_can_authenticate(user)
        if not is_allowed:
            return False

        if not isinstance(user, Employee):
            return True

        return user.status != Employee.Status.DEACTIVATED
