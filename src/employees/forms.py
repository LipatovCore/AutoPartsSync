from django.contrib.auth.forms import AuthenticationForm
from django.forms import EmailField, EmailInput, PasswordInput


class EmployeeAuthenticationForm(AuthenticationForm):
    username = EmailField(
        label="Email",
        widget=EmailInput(
            attrs={
                "autofocus": True,
                "autocomplete": "email",
                "placeholder": "name@example.com",
            }
        ),
    )

    password = AuthenticationForm.base_fields["password"].__class__(
        label="Пароль",
        strip=False,
        widget=PasswordInput(
            attrs={
                "autocomplete": "current-password",
                "placeholder": "Введите пароль",
            }
        ),
    )
