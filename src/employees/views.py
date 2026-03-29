from django.contrib.auth.views import LoginView

from .forms import EmployeeAuthenticationForm


class EmployeeLoginView(LoginView):
    authentication_form = EmployeeAuthenticationForm
