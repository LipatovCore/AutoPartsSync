from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q

from .managers import EmployeeManager


class Employee(AbstractUser):
    class Status(models.TextChoices):
        CREATED = "created", "Создан"
        ACTIVE = "active", "Активен"
        DEACTIVATED = "deactivated", "Деактивирован"

    username = None
    email = models.EmailField("Email", unique=True)
    status = models.CharField(
        "Статус доступа",
        max_length=16,
        choices=Status.choices,
        default=Status.CREATED,
    )
    email_verified = models.BooleanField("Email подтвержден", default=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлен", auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = EmployeeManager()

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"
        ordering = ["email"]

    def __str__(self):
        return self.email


class EmployeeInvitation(models.Model):
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="invitations",
        verbose_name="Сотрудник",
    )
    token_hash = models.CharField("Хеш токена", max_length=128, unique=True)
    expires_at = models.DateTimeField("Истекает")
    used_at = models.DateTimeField("Использован", blank=True, null=True)
    revoked_at = models.DateTimeField("Отозван", blank=True, null=True)
    issued_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="issued_employee_invitations",
        verbose_name="Кем выдано",
    )
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлен", auto_now=True)

    class Meta:
        verbose_name = "Приглашение сотрудника"
        verbose_name_plural = "Приглашения сотрудников"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["employee"],
                condition=Q(used_at__isnull=True, revoked_at__isnull=True),
                name="unique_active_employee_invitation",
            ),
        ]
        indexes = [
            models.Index(fields=["employee", "expires_at"], name="employee_invite_exp_idx"),
        ]

    def __str__(self):
        return f"Invitation for {self.employee.email}"
