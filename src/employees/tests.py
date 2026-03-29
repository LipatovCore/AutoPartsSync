from datetime import timedelta
import hashlib

from django.conf import settings
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from employees.models import Employee, EmployeeInvitation
from employees.services.invitation_service import (
    EmployeeInvitationService,
    EmployeeInvitationServiceError,
)


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


class EmployeeInvitationServiceTests(TestCase):
    def setUp(self):
        self.service = EmployeeInvitationService()
        self.issuer = Employee.objects.create_superuser(
            email="issuer@example.com",
            password="safe-password-123",
        )

    def test_create_employee_invitation_creates_employee_and_hashed_invitation(self):
        before_call = timezone.now()

        result = self.service.create_employee_invitation(
            email="new.employee@example.com",
            issued_by=self.issuer,
        )

        self.assertTrue(result.created_employee)
        self.assertEqual(result.employee.status, Employee.Status.CREATED)
        self.assertFalse(result.employee.has_usable_password())
        self.assertEqual(
            result.invitation.token_hash,
            hashlib.sha256(result.raw_token.encode("utf-8")).hexdigest(),
        )
        self.assertAlmostEqual(
            result.invitation.expires_at.timestamp(),
            (before_call + settings.EMPLOYEE_INVITATION_TTL).timestamp(),
            delta=5,
        )

    def test_reissue_revokes_previous_invitation_and_creates_new_one(self):
        employee = Employee.objects.create_user(
            email="created@example.com",
            password=None,
            status=Employee.Status.CREATED,
        )
        first_result = self.service.reissue_employee_invitation(
            employee_id=employee.pk,
            issued_by=self.issuer,
        )

        second_result = self.service.reissue_employee_invitation(
            employee_id=employee.pk,
            issued_by=self.issuer,
        )

        first_result.invitation.refresh_from_db()

        self.assertIsNotNone(first_result.invitation.revoked_at)
        self.assertNotEqual(first_result.raw_token, second_result.raw_token)
        self.assertEqual(
            EmployeeInvitation.objects.filter(
                employee=employee,
                used_at__isnull=True,
                revoked_at__isnull=True,
            ).count(),
            1,
        )

    def test_create_employee_invitation_rejects_active_employee(self):
        Employee.objects.create_user(
            email="active@example.com",
            password="safe-password-123",
            status=Employee.Status.ACTIVE,
        )

        with self.assertRaisesMessage(
            EmployeeInvitationServiceError,
            "Приглашение можно перевыпускать только для сотрудников со статусом created.",
        ):
            self.service.create_employee_invitation(
                email="active@example.com",
                issued_by=self.issuer,
            )

    def test_reissue_employee_invitation_rejects_deactivated_employee(self):
        employee = Employee.objects.create_user(
            email="deactivated@example.com",
            password=None,
            status=Employee.Status.DEACTIVATED,
        )

        with self.assertRaisesMessage(
            EmployeeInvitationServiceError,
            "Перевыпуск доступен только для сотрудников со статусом created.",
        ):
            self.service.reissue_employee_invitation(
                employee_id=employee.pk,
                issued_by=self.issuer,
            )


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


class EmployeeManagementViewTests(TestCase):
    def setUp(self):
        self.password = "safe-password-123"
        self.admin_employee = Employee.objects.create_superuser(
            email="admin@example.com",
            password=self.password,
        )
        self.regular_employee = Employee.objects.create_user(
            email="worker@example.com",
            password=self.password,
            status=Employee.Status.ACTIVE,
        )

    def test_employee_management_requires_login(self):
        response = self.client.get(reverse("employees:list"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_employee_management_is_forbidden_for_non_admin(self):
        self.client.force_login(self.regular_employee)

        response = self.client.get(reverse("employees:list"))

        self.assertEqual(response.status_code, 403)

    def test_admin_can_create_employee_and_see_invitation_link(self):
        self.client.force_login(self.admin_employee)

        response = self.client.post(
            reverse("employees:create"),
            {"email": "invited@example.com"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Сотрудник создан, приглашение выпущено.")
        self.assertContains(response, "invited@example.com")

        employee = Employee.objects.get(email="invited@example.com")
        invitation = EmployeeInvitation.objects.get(employee=employee)

        self.assertContains(
            response,
            f"/employees/invitations/",
        )
        self.assertNotContains(response, invitation.token_hash)
        self.assertEqual(employee.status, Employee.Status.CREATED)

    def test_admin_can_reissue_invitation_and_previous_token_is_revoked(self):
        self.client.force_login(self.admin_employee)
        employee = Employee.objects.create_user(
            email="created@example.com",
            password=None,
            status=Employee.Status.CREATED,
        )
        current_invitation = EmployeeInvitation.objects.create(
            employee=employee,
            issued_by=self.admin_employee,
            token_hash="old-hash",
            expires_at=timezone.now() + timedelta(hours=1),
        )

        response = self.client.post(
            reverse("employees:reissue-invitation", args=[employee.pk]),
            follow=True,
        )

        current_invitation.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Приглашение перевыпущено.")
        self.assertIsNotNone(current_invitation.revoked_at)
        self.assertEqual(
            EmployeeInvitation.objects.filter(
                employee=employee,
                used_at__isnull=True,
                revoked_at__isnull=True,
            ).count(),
            1,
        )

    def test_admin_cannot_reissue_invitation_for_active_employee(self):
        self.client.force_login(self.admin_employee)

        response = self.client.post(
            reverse("employees:create"),
            {"email": self.regular_employee.email},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Приглашение можно перевыпускать только для сотрудников со статусом created.",
        )
