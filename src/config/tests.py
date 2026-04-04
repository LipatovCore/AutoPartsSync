import os
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from config import settings


class SettingsHelpersTests(SimpleTestCase):
    def test_local_environment_keeps_debug_enabled_by_default(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertTrue(settings.get_debug_setting(settings.LOCAL_ENVIRONMENT))

    def test_non_local_environment_forces_debug_off(self):
        with patch.dict(os.environ, {"DJANGO_DEBUG": "True"}, clear=True):
            self.assertFalse(settings.get_debug_setting("staging"))
            self.assertFalse(settings.get_debug_setting(settings.PRODUCTION_ENVIRONMENT))

    def test_local_environment_uses_safe_default_allowed_hosts(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(
                settings.get_allowed_hosts(
                    settings.LOCAL_ENVIRONMENT,
                    debug_enabled=True,
                ),
                ["127.0.0.1", "localhost"],
            )

    def test_non_local_environment_requires_allowed_hosts(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesMessage(
                ImproperlyConfigured,
                "DJANGO_ALLOWED_HOSTS must be configured outside local development.",
            ):
                settings.get_allowed_hosts("staging", debug_enabled=False)

    def test_local_environment_uses_fallback_secret_key(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(
                settings.get_secret_key(settings.LOCAL_ENVIRONMENT),
                "unsafe-local-development-key",
            )

    def test_non_local_environment_requires_secret_key(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesMessage(
                ImproperlyConfigured,
                "DJANGO_SECRET_KEY must be configured outside local development.",
            ):
                settings.get_secret_key(settings.PRODUCTION_ENVIRONMENT)

    def test_production_environment_enables_secure_cookie_and_https_settings(self):
        security_settings = settings.get_security_settings(
            settings.PRODUCTION_ENVIRONMENT
        )

        self.assertTrue(security_settings["SECURE_SSL_REDIRECT"])
        self.assertTrue(security_settings["SESSION_COOKIE_SECURE"])
        self.assertTrue(security_settings["CSRF_COOKIE_SECURE"])
        self.assertEqual(
            security_settings["SECURE_PROXY_SSL_HEADER"],
            ("HTTP_X_FORWARDED_PROTO", "https"),
        )

    def test_local_environment_disables_production_only_security_flags(self):
        security_settings = settings.get_security_settings(settings.LOCAL_ENVIRONMENT)

        self.assertFalse(security_settings["SECURE_SSL_REDIRECT"])
        self.assertFalse(security_settings["SESSION_COOKIE_SECURE"])
        self.assertFalse(security_settings["CSRF_COOKIE_SECURE"])
        self.assertIsNone(security_settings["SECURE_PROXY_SSL_HEADER"])
