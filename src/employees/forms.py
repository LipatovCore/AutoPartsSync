from django import forms
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
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


class EmployeeInvitationIssueForm(forms.Form):
    email = EmailField(
        label="Email сотрудника",
        widget=EmailInput(
            attrs={
                "autocomplete": "email",
                "placeholder": "employee@example.com",
            }
        ),
    )


class EmployeePasswordSetupForm(SetPasswordForm):
    error_messages = {
        "password_mismatch": "Введенные пароли не совпадают.",
    }

    new_password1 = forms.CharField(
        label="Новый пароль",
        strip=False,
        widget=PasswordInput(
            attrs={
                "autocomplete": "new-password",
                "placeholder": "Придумайте пароль",
            }
        ),
    )
    new_password2 = forms.CharField(
        label="Подтверждение пароля",
        strip=False,
        widget=PasswordInput(
            attrs={
                "autocomplete": "new-password",
                "placeholder": "Повторите пароль",
            }
        ),
    )
