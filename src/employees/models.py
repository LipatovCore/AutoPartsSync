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
        permissions = [
            (
                "manage_employee_access",
                "Can manage employee invitations and access state",
            ),
            (
                "view_employee_access_audit",
                "Can view employee access audit log",
            ),
        ]

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


class EmployeeAccessAuditEvent(models.Model):
    class EventType(models.TextChoices):
        EMPLOYEE_CREATED = "employee_created", "Сотрудник создан"
        INVITATION_ISSUED = "invitation_issued", "Приглашение выпущено"
        INVITATION_REVOKED = "invitation_revoked", "Приглашение отозвано"
        ACTIVATION_SUCCEEDED = "activation_succeeded", "Активация успешна"
        ACTIVATION_FAILED = "activation_failed", "Активация неуспешна"
        ACCESS_RESET = "access_reset", "Доступ сброшен"
        EMPLOYEE_DEACTIVATED = "employee_deactivated", "Сотрудник деактивирован"

    event_type = models.CharField(
        "Тип события",
        max_length=32,
        choices=EventType.choices,
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        related_name="access_audit_events",
        verbose_name="Сотрудник",
        blank=True,
        null=True,
    )
    actor = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        related_name="performed_access_audit_events",
        verbose_name="Инициатор",
        blank=True,
        null=True,
    )
    invitation = models.ForeignKey(
        EmployeeInvitation,
        on_delete=models.SET_NULL,
        related_name="audit_events",
        verbose_name="Приглашение",
        blank=True,
        null=True,
    )
    ip_address = models.GenericIPAddressField(
        "IP-адрес",
        blank=True,
        null=True,
    )
    metadata = models.JSONField("Метаданные", default=dict, blank=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        verbose_name = "Событие аудита доступа"
        verbose_name_plural = "События аудита доступа"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["event_type", "created_at"], name="employee_audit_type_idx"),
            models.Index(fields=["employee", "created_at"], name="employee_audit_emp_idx"),
        ]

    def __str__(self):
        return self.get_event_type_display()
