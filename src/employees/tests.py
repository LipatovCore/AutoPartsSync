from datetime import timedelta

from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from employees.models import Employee, EmployeeInvitation


class EmployeeManagerTests(TestCase):
    def test_create_user_uses_email_as_login_identifier(self):
        employee = Employee.objects.create_user(
            email="Worker@Example.com",
            password="safe-password-123",
        )

        self.assertEqual(employee.email, "Worker@example.com")
        self.assertEqual(employee.status, Employee.Status.CREATED)
        self.assertTrue(employee.email_verified)
        self.assertFalse(employee.is_staff)
        self.assertFalse(employee.is_superuser)
        self.assertTrue(employee.check_password("safe-password-123"))

    def test_create_user_requires_email(self):
        with self.assertRaisesMessage(ValueError, "The email address must be set."):
            Employee.objects.create_user(email="", password="safe-password-123")

    def test_create_superuser_sets_required_flags(self):
        admin = Employee.objects.create_superuser(
            email="admin@example.com",
            password="safe-password-123",
        )

        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertEqual(admin.status, Employee.Status.ACTIVE)


class EmployeeInvitationModelTests(TestCase):
    def setUp(self):
        self.employee = Employee.objects.create_user(
            email="employee@example.com",
            password="safe-password-123",
        )
        self.issuer = Employee.objects.create_superuser(
            email="issuer@example.com",
            password="safe-password-123",
        )

    def test_only_one_unfinished_invitation_can_exist_for_employee(self):
        EmployeeInvitation.objects.create(
            employee=self.employee,
            issued_by=self.issuer,
            token_hash="hash-1",
            expires_at=timezone.now() + timedelta(days=1),
        )

        with self.assertRaises(IntegrityError):
            EmployeeInvitation.objects.create(
                employee=self.employee,
                issued_by=self.issuer,
                token_hash="hash-2",
                expires_at=timezone.now() + timedelta(days=1),
            )

    def test_new_invitation_can_be_created_after_previous_is_revoked(self):
        invitation = EmployeeInvitation.objects.create(
            employee=self.employee,
            issued_by=self.issuer,
            token_hash="hash-1",
            expires_at=timezone.now() + timedelta(days=1),
        )
        invitation.revoked_at = timezone.now()
        invitation.save(update_fields=["revoked_at", "updated_at"])

        replacement = EmployeeInvitation.objects.create(
            employee=self.employee,
            issued_by=self.issuer,
            token_hash="hash-2",
            expires_at=timezone.now() + timedelta(days=1),
        )

        self.assertEqual(replacement.employee, self.employee)

