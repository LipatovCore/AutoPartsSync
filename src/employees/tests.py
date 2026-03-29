from datetime import timedelta

from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

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


class EmployeeLoginTests(TestCase):
    def setUp(self):
        self.password = "safe-password-123"
        self.active_employee = Employee.objects.create_user(
            email="active@example.com",
            password=self.password,
            status=Employee.Status.ACTIVE,
        )
        self.deactivated_employee = Employee.objects.create_user(
            email="deactivated@example.com",
            password=self.password,
            status=Employee.Status.DEACTIVATED,
        )
        self.admin_employee = Employee.objects.create_superuser(
            email="admin@example.com",
            password=self.password,
        )

    def test_login_page_uses_email_field(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'type="email"', html=False)
        self.assertContains(response, "name=\"username\"", html=False)
        self.assertContains(response, "Email")

    def test_active_employee_can_log_in_with_email_and_password(self):
        response = self.client.post(
            reverse("login"),
            {
                "username": self.active_employee.email,
                "password": self.password,
            },
        )

        self.assertRedirects(response, "/analogs/")
        self.assertEqual(
            int(self.client.session["_auth_user_id"]),
            self.active_employee.pk,
        )

    def test_deactivated_employee_cannot_log_in(self):
        response = self.client.post(
            reverse("login"),
            {
                "username": self.deactivated_employee.email,
                "password": self.password,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Не удалось выполнить вход")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_admin_index_is_available_only_to_admins(self):
        self.client.force_login(self.active_employee)

        response = self.client.get("/admin/")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_admin_can_open_admin_index(self):
        self.client.force_login(self.admin_employee)

        response = self.client.get("/admin/")

        self.assertEqual(response.status_code, 200)
