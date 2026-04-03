from datetime import timedelta
import hashlib

from django.conf import settings
from django.contrib.auth import SESSION_KEY, get_user_model
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.db import IntegrityError
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone

from employees.models import Employee, EmployeeAccessAuditEvent, EmployeeInvitation
from employees.services.access_service import (
    EmployeeAccessService,
    EmployeeAccessServiceError,
)
from employees.services.invitation_service import (
    EmployeeInvitationService,
    EmployeeInvitationServiceError,
)
from employees.services.password_setup_service import (
    EmployeePasswordSetupService,
    EmployeePasswordSetupServiceError,
)
from employees.services.session_service import EmployeeSessionService


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
        self.assertEqual(
            list(
                EmployeeAccessAuditEvent.objects.values_list("event_type", flat=True)
            ),
            [
                EmployeeAccessAuditEvent.EventType.INVITATION_ISSUED,
                EmployeeAccessAuditEvent.EventType.EMPLOYEE_CREATED,
            ],
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
        self.assertEqual(
            list(
                EmployeeAccessAuditEvent.objects.filter(employee=employee).values_list(
                    "event_type",
                    flat=True,
                )
            )[:2],
            [
                EmployeeAccessAuditEvent.EventType.INVITATION_ISSUED,
                EmployeeAccessAuditEvent.EventType.INVITATION_REVOKED,
            ],
        )

    def test_create_employee_invitation_rejects_active_employee(self):
        Employee.objects.create_user(
            email="active@example.com",
            password="safe-password-123",
            status=Employee.Status.ACTIVE,
        )

        with self.assertRaises(EmployeeInvitationServiceError):
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

        with self.assertRaises(EmployeeInvitationServiceError):
            self.service.reissue_employee_invitation(
                employee_id=employee.pk,
                issued_by=self.issuer,
            )


class EmployeePasswordSetupServiceTests(TestCase):
    def setUp(self):
        self.service = EmployeePasswordSetupService()
        self.issuer = Employee.objects.create_superuser(
            email="issuer@example.com",
            password="safe-password-123",
        )
        self.employee = Employee.objects.create_user(
            email="created@example.com",
            password=None,
            status=Employee.Status.CREATED,
        )
        self.raw_token = "valid-token"
        self.invitation = EmployeeInvitation.objects.create(
            employee=self.employee,
            issued_by=self.issuer,
            token_hash=hashlib.sha256(self.raw_token.encode("utf-8")).hexdigest(),
            expires_at=timezone.now() + timedelta(hours=1),
        )

    def test_activate_employee_with_password_marks_invitation_used_and_activates_employee(self):
        session = SessionStore()
        session[SESSION_KEY] = str(self.employee.pk)
        session.create()

        self.service.activate_employee_with_password(
            raw_token=self.raw_token,
            password="Complex-pass-123",
        )

        self.employee.refresh_from_db()
        self.invitation.refresh_from_db()

        self.assertEqual(self.employee.status, Employee.Status.ACTIVE)
        self.assertTrue(self.employee.check_password("Complex-pass-123"))
        self.assertIsNotNone(self.invitation.used_at)
        self.assertFalse(
            Session.objects.filter(session_key=session.session_key).exists()
        )
        self.assertTrue(
            EmployeeAccessAuditEvent.objects.filter(
                event_type=EmployeeAccessAuditEvent.EventType.ACTIVATION_SUCCEEDED,
                employee=self.employee,
                invitation=self.invitation,
            ).exists()
        )

    def test_activate_employee_with_password_rejects_expired_invitation(self):
        self.invitation.expires_at = timezone.now() - timedelta(seconds=1)
        self.invitation.save(update_fields=["expires_at", "updated_at"])

        with self.assertRaisesMessage(
            EmployeePasswordSetupServiceError,
            self.service.INVALID_LINK_MESSAGE,
        ):
            self.service.activate_employee_with_password(
                raw_token=self.raw_token,
                password="Complex-pass-123",
            )

    def test_activate_employee_with_password_rejects_non_created_employee(self):
        self.employee.status = Employee.Status.ACTIVE
        self.employee.save(update_fields=["status", "updated_at"])

        with self.assertRaisesMessage(
            EmployeePasswordSetupServiceError,
            self.service.INVALID_LINK_MESSAGE,
        ):
            self.service.activate_employee_with_password(
                raw_token=self.raw_token,
                password="Complex-pass-123",
            )


class EmployeeAccessServiceTests(TestCase):
    def setUp(self):
        self.service = EmployeeAccessService()
        self.admin_employee = Employee.objects.create_superuser(
            email="admin@example.com",
            password="safe-password-123",
        )
        self.target_employee = Employee.objects.create_user(
            email="active@example.com",
            password="safe-password-123",
            status=Employee.Status.ACTIVE,
        )

    def test_deactivate_employee_changes_status_terminates_sessions_and_records_audit(self):
        session = SessionStore()
        session[SESSION_KEY] = str(self.target_employee.pk)
        session.create()

        self.service.deactivate_employee(
            employee_id=self.target_employee.pk,
            actor=self.admin_employee,
            ip_address="127.0.0.1",
        )

        self.target_employee.refresh_from_db()

        self.assertEqual(self.target_employee.status, Employee.Status.DEACTIVATED)
        self.assertFalse(
            Session.objects.filter(session_key=session.session_key).exists()
        )
        self.assertTrue(
            EmployeeAccessAuditEvent.objects.filter(
                event_type=EmployeeAccessAuditEvent.EventType.EMPLOYEE_DEACTIVATED,
                employee=self.target_employee,
                actor=self.admin_employee,
                ip_address="127.0.0.1",
            ).exists()
        )

    def test_deactivate_employee_rejects_self_deactivation(self):
        with self.assertRaisesMessage(
            EmployeeAccessServiceError,
            "Нельзя деактивировать собственную учетную запись.",
        ):
            self.service.deactivate_employee(
                employee_id=self.admin_employee.pk,
                actor=self.admin_employee,
            )

    def test_deactivate_employee_rejects_already_deactivated_employee(self):
        self.target_employee.status = Employee.Status.DEACTIVATED
        self.target_employee.save(update_fields=["status", "updated_at"])

        with self.assertRaisesMessage(
            EmployeeAccessServiceError,
            "Сотрудник уже деактивирован.",
        ):
            self.service.deactivate_employee(
                employee_id=self.target_employee.pk,
                actor=self.admin_employee,
            )

    def test_reset_employee_access_creates_new_invitation_and_records_audit(self):
        session = SessionStore()
        session[SESSION_KEY] = str(self.target_employee.pk)
        session.create()
        existing_invitation = EmployeeInvitation.objects.create(
            employee=self.target_employee,
            issued_by=self.admin_employee,
            token_hash="old-reset-token-hash",
            expires_at=timezone.now() + timedelta(hours=1),
        )

        result = self.service.reset_employee_access(
            employee_id=self.target_employee.pk,
            actor=self.admin_employee,
            ip_address="127.0.0.1",
        )

        self.target_employee.refresh_from_db()
        existing_invitation.refresh_from_db()

        self.assertEqual(self.target_employee.status, Employee.Status.CREATED)
        self.assertFalse(self.target_employee.has_usable_password())
        self.assertFalse(
            Session.objects.filter(session_key=session.session_key).exists()
        )
        self.assertIsNotNone(existing_invitation.revoked_at)
        self.assertEqual(
            hashlib.sha256(result.raw_token.encode("utf-8")).hexdigest(),
            result.invitation.token_hash,
        )
        self.assertEqual(
            EmployeeInvitation.objects.filter(
                employee=self.target_employee,
                used_at__isnull=True,
                revoked_at__isnull=True,
            ).count(),
            1,
        )
        self.assertTrue(
            EmployeeAccessAuditEvent.objects.filter(
                event_type=EmployeeAccessAuditEvent.EventType.ACCESS_RESET,
                employee=self.target_employee,
                actor=self.admin_employee,
                invitation=result.invitation,
                ip_address="127.0.0.1",
            ).exists()
        )
        self.assertTrue(
            EmployeeAccessAuditEvent.objects.filter(
                event_type=EmployeeAccessAuditEvent.EventType.INVITATION_REVOKED,
                employee=self.target_employee,
                invitation=existing_invitation,
            ).exists()
        )
        self.assertTrue(
            EmployeeAccessAuditEvent.objects.filter(
                event_type=EmployeeAccessAuditEvent.EventType.INVITATION_ISSUED,
                employee=self.target_employee,
                invitation=result.invitation,
            ).exists()
        )

    def test_reset_employee_access_rejects_non_active_employee(self):
        self.target_employee.status = Employee.Status.CREATED
        self.target_employee.save(update_fields=["status", "updated_at"])

        with self.assertRaisesMessage(
            EmployeeAccessServiceError,
            "Сброс доступа доступен только для активных сотрудников.",
        ):
            self.service.reset_employee_access(
                employee_id=self.target_employee.pk,
                actor=self.admin_employee,
            )

    def test_reset_employee_access_rejects_self_reset(self):
        with self.assertRaisesMessage(
            EmployeeAccessServiceError,
            "Нельзя сбрасывать доступ для собственной учетной записи.",
        ):
            self.service.reset_employee_access(
                employee_id=self.admin_employee.pk,
                actor=self.admin_employee,
            )


class EmployeeSessionServiceTests(TestCase):
    def setUp(self):
        self.service = EmployeeSessionService()
        self.employee = Employee.objects.create_user(
            email="active@example.com",
            password="safe-password-123",
            status=Employee.Status.ACTIVE,
        )
        self.other_employee = Employee.objects.create_user(
            email="other@example.com",
            password="safe-password-123",
            status=Employee.Status.ACTIVE,
        )

    def _create_session_for_employee(self, employee: Employee) -> str:
        session = SessionStore()
        session[SESSION_KEY] = str(employee.pk)
        session.create()
        return session.session_key

    def test_terminate_employee_sessions_deletes_only_target_employee_sessions(self):
        target_session_key = self._create_session_for_employee(self.employee)
        other_session_key = self._create_session_for_employee(self.other_employee)

        deleted_count = self.service.terminate_employee_sessions(employee=self.employee)

        self.assertEqual(deleted_count, 1)
        self.assertFalse(Session.objects.filter(session_key=target_session_key).exists())
        self.assertTrue(Session.objects.filter(session_key=other_session_key).exists())

    def test_terminate_employee_sessions_returns_zero_when_employee_has_no_sessions(self):
        other_session_key = self._create_session_for_employee(self.other_employee)

        deleted_count = self.service.terminate_employee_sessions(employee=self.employee)

        self.assertEqual(deleted_count, 0)
        self.assertTrue(Session.objects.filter(session_key=other_session_key).exists())


class EmployeeLoginTests(TestCase):
    def setUp(self):
        cache.clear()
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
        self.assertContains(response, 'name="username"', html=False)
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
        cache.clear()
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
        self.assertContains(response, "invited@example.com")

        employee = Employee.objects.get(email="invited@example.com")
        invitation = EmployeeInvitation.objects.get(employee=employee)

        self.assertContains(response, "/employees/invitations/")
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
        self.assertEqual(
            EmployeeInvitation.objects.filter(employee=self.regular_employee).count(),
            0,
        )

    def test_admin_can_deactivate_employee_and_terminate_sessions(self):
        session = SessionStore()
        session[SESSION_KEY] = str(self.regular_employee.pk)
        session.create()
        self.client.force_login(self.admin_employee)

        response = self.client.post(
            reverse("employees:deactivate", args=[self.regular_employee.pk]),
            follow=True,
        )

        self.regular_employee.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.regular_employee.status, Employee.Status.DEACTIVATED)
        self.assertFalse(
            Session.objects.filter(session_key=session.session_key).exists()
        )
        self.assertTrue(
            EmployeeAccessAuditEvent.objects.filter(
                event_type=EmployeeAccessAuditEvent.EventType.EMPLOYEE_DEACTIVATED,
                employee=self.regular_employee,
                actor=self.admin_employee,
            ).exists()
        )

    def test_admin_cannot_deactivate_self(self):
        self.client.force_login(self.admin_employee)

        response = self.client.post(
            reverse("employees:deactivate", args=[self.admin_employee.pk]),
            follow=True,
        )

        self.admin_employee.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.admin_employee.status, Employee.Status.ACTIVE)
        self.assertContains(response, "Нельзя деактивировать собственную учетную запись.")

    def test_admin_can_reset_active_employee_access(self):
        session = SessionStore()
        session[SESSION_KEY] = str(self.regular_employee.pk)
        session.create()
        self.client.force_login(self.admin_employee)

        response = self.client.post(
            reverse("employees:reset-access", args=[self.regular_employee.pk]),
            follow=True,
        )

        self.regular_employee.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.regular_employee.status, Employee.Status.CREATED)
        self.assertFalse(self.regular_employee.has_usable_password())
        self.assertFalse(
            Session.objects.filter(session_key=session.session_key).exists()
        )
        self.assertContains(
            response,
            "Доступ сотрудника сброшен. Новая ссылка на установку пароля готова.",
        )
        self.assertContains(response, self.regular_employee.email)
        self.assertContains(response, "/employees/invitations/")
        self.assertTrue(
            EmployeeAccessAuditEvent.objects.filter(
                event_type=EmployeeAccessAuditEvent.EventType.ACCESS_RESET,
                employee=self.regular_employee,
                actor=self.admin_employee,
            ).exists()
        )

    def test_admin_cannot_reset_own_access(self):
        self.client.force_login(self.admin_employee)

        response = self.client.post(
            reverse("employees:reset-access", args=[self.admin_employee.pk]),
            follow=True,
        )

        self.admin_employee.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.admin_employee.status, Employee.Status.ACTIVE)
        self.assertContains(
            response,
            "Нельзя сбрасывать доступ для собственной учетной записи.",
        )


class EmployeePasswordSetupViewTests(TestCase):
    def setUp(self):
        cache.clear()
        self.password = "safe-password-123"
        self.user_model = get_user_model()
        self.issuer = self.user_model.objects.create_superuser(
            email="admin@example.com",
            password=self.password,
        )
        self.employee = self.user_model.objects.create_user(
            email="created@example.com",
            password=None,
            status=Employee.Status.CREATED,
        )
        self.raw_token = "view-token"
        self.invitation = EmployeeInvitation.objects.create(
            employee=self.employee,
            issued_by=self.issuer,
            token_hash=hashlib.sha256(self.raw_token.encode("utf-8")).hexdigest(),
            expires_at=timezone.now() + timedelta(hours=1),
        )

    def test_valid_token_renders_password_setup_form(self):
        response = self.client.get(
            reverse("employees:set-password", args=[self.raw_token])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="new_password1"', html=False)
        self.assertContains(response, 'name="new_password2"', html=False)

    def test_invalid_token_shows_generic_error_message(self):
        response = self.client.get(
            reverse("employees:set-password", args=["unknown-token"])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            EmployeePasswordSetupService.INVALID_LINK_MESSAGE,
        )
        self.assertNotContains(response, 'name="new_password1"', html=False)
        failed_event = EmployeeAccessAuditEvent.objects.get(
            event_type=EmployeeAccessAuditEvent.EventType.ACTIVATION_FAILED
        )
        self.assertEqual(
            failed_event.metadata["token_hash"],
            hashlib.sha256("unknown-token".encode("utf-8")).hexdigest(),
        )
        self.assertEqual(failed_event.metadata["reason"], "invalid_link")

    def test_successful_password_setup_redirects_to_login_and_activates_employee(self):
        session = SessionStore()
        session[SESSION_KEY] = str(self.employee.pk)
        session.create()

        response = self.client.post(
            reverse("employees:set-password", args=[self.raw_token]),
            {
                "new_password1": "Complex-pass-123",
                "new_password2": "Complex-pass-123",
            },
            follow=True,
        )

        self.employee.refresh_from_db()
        self.invitation.refresh_from_db()

        self.assertRedirects(response, reverse("login"))
        self.assertEqual(self.employee.status, Employee.Status.ACTIVE)
        self.assertTrue(self.employee.check_password("Complex-pass-123"))
        self.assertIsNotNone(self.invitation.used_at)
        self.assertFalse(
            Session.objects.filter(session_key=session.session_key).exists()
        )

    def test_used_token_cannot_be_reused(self):
        self.client.post(
            reverse("employees:set-password", args=[self.raw_token]),
            {
                "new_password1": "Complex-pass-123",
                "new_password2": "Complex-pass-123",
            },
        )

        response = self.client.get(
            reverse("employees:set-password", args=[self.raw_token])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            EmployeePasswordSetupService.INVALID_LINK_MESSAGE,
        )

    def test_expired_token_is_rejected(self):
        self.invitation.expires_at = timezone.now() - timedelta(minutes=1)
        self.invitation.save(update_fields=["expires_at", "updated_at"])

        response = self.client.get(
            reverse("employees:set-password", args=[self.raw_token])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            EmployeePasswordSetupService.INVALID_LINK_MESSAGE,
        )

    def test_invalid_password_shows_form_errors_without_activating_employee(self):
        response = self.client.post(
            reverse("employees:set-password", args=[self.raw_token]),
            {
                "new_password1": "123",
                "new_password2": "321",
            },
        )

        self.employee.refresh_from_db()
        self.invitation.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="new_password1"', html=False)
        self.assertEqual(self.employee.status, Employee.Status.CREATED)
        self.assertIsNone(self.invitation.used_at)

@override_settings(
    EMPLOYEE_AUTH_RATE_LIMITS={
        "login": {"attempts": 2, "window_seconds": 60, "block_seconds": 120},
        "password_setup": {"attempts": 2, "window_seconds": 60, "block_seconds": 120},
        "invitation_reissue": {
            "attempts": 2,
            "window_seconds": 60,
            "block_seconds": 120,
        },
    }
)
class EmployeeAuthRateLimitTests(TestCase):
    def setUp(self):
        cache.clear()
        self.password = "safe-password-123"
        self.admin_employee = Employee.objects.create_superuser(
            email="admin@example.com",
            password=self.password,
        )
        self.active_employee = Employee.objects.create_user(
            email="active@example.com",
            password=self.password,
            status=Employee.Status.ACTIVE,
        )
        self.created_employee = Employee.objects.create_user(
            email="created@example.com",
            password=None,
            status=Employee.Status.CREATED,
        )
        self.raw_token = "rate-limit-token"
        self.invitation = EmployeeInvitation.objects.create(
            employee=self.created_employee,
            issued_by=self.admin_employee,
            token_hash=hashlib.sha256(self.raw_token.encode("utf-8")).hexdigest(),
            expires_at=timezone.now() + timedelta(hours=1),
        )

    def test_login_is_limited_by_ip_and_email_with_wait_time_message(self):
        payload = {
            "username": self.active_employee.email,
            "password": "wrong-password",
        }

        self.client.post(reverse("login"), payload)
        self.client.post(reverse("login"), payload)
        response = self.client.post(reverse("login"), payload)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Превышен лимит попыток входа")
        self.assertContains(response, "120 сек")

    def test_invalid_login_shows_remaining_attempts(self):
        response = self.client.post(
            reverse("login"),
            {
                "username": self.active_employee.email,
                "password": "wrong-password",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Не удалось выполнить вход. Проверьте email и пароль.")
        self.assertContains(response, "Осталось попыток: 1.")

    def test_successful_login_resets_login_rate_limit(self):
        payload = {
            "username": self.active_employee.email,
            "password": "wrong-password",
        }
        self.client.post(reverse("login"), payload)

        success_response = self.client.post(
            reverse("login"),
            {
                "username": self.active_employee.email,
                "password": self.password,
            },
        )
        self.assertRedirects(success_response, "/analogs/")

        first_response_after_success = self.client.post(reverse("login"), payload)
        second_response_after_success = self.client.post(reverse("login"), payload)
        blocked_response = self.client.post(reverse("login"), payload)

        self.assertEqual(first_response_after_success.status_code, 200)
        self.assertEqual(second_response_after_success.status_code, 200)
        self.assertNotContains(
            second_response_after_success,
            "Превышен лимит попыток входа",
        )
        self.assertContains(blocked_response, "Превышен лимит попыток входа")

    def test_password_setup_is_limited_by_ip_and_token_with_wait_time_message(self):
        url = reverse("employees:set-password", args=[self.raw_token])

        self.client.get(url)
        self.client.get(url)
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Превышен лимит попыток установки пароля")
        self.assertContains(response, "120 сек")

    def test_reissue_is_limited_by_ip_and_employee_id_with_wait_time_message(self):
        self.client.force_login(self.admin_employee)

        reissue_url = reverse(
            "employees:reissue-invitation",
            args=[self.created_employee.pk],
        )
        self.client.post(reissue_url, follow=True)
        self.client.post(reissue_url, follow=True)
        response = self.client.post(reissue_url, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Превышен лимит попыток перевыпуска приглашения")
        self.assertContains(response, "120 сек")
