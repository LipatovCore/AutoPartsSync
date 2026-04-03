from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import hashlib
import math

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    retry_after_seconds: int


class EmployeeSecurityService:
    def check_rate_limit(
        self,
        *,
        scope: str,
        ip_address: str,
        identifier: str,
    ) -> RateLimitResult:
        rate_limit_config = settings.EMPLOYEE_AUTH_RATE_LIMITS[scope]
        blocked_until = self._get_blocked_until(
            scope=scope,
            ip_address=ip_address,
            identifier=identifier,
        )
        if blocked_until is not None:
            return RateLimitResult(
                allowed=False,
                retry_after_seconds=self._seconds_until(blocked_until),
            )

        counter_key = self._build_counter_key(
            scope=scope,
            ip_address=ip_address,
            identifier=identifier,
        )
        attempts = self._increment_counter(
            key=counter_key,
            window_seconds=rate_limit_config["window_seconds"],
        )
        if attempts <= rate_limit_config["attempts"]:
            return RateLimitResult(allowed=True, retry_after_seconds=0)

        blocked_until = timezone.now() + timedelta(
            seconds=rate_limit_config["block_seconds"]
        )
        cache.set(
            self._build_block_key(
                scope=scope,
                ip_address=ip_address,
                identifier=identifier,
            ),
            blocked_until.timestamp(),
            timeout=rate_limit_config["block_seconds"],
        )
        return RateLimitResult(
            allowed=False,
            retry_after_seconds=rate_limit_config["block_seconds"],
        )

    def reset_rate_limit(
        self,
        *,
        scope: str,
        ip_address: str,
        identifier: str,
    ) -> None:
        cache.delete(
            self._build_counter_key(
                scope=scope,
                ip_address=ip_address,
                identifier=identifier,
            )
        )
        cache.delete(
            self._build_block_key(
                scope=scope,
                ip_address=ip_address,
                identifier=identifier,
            )
        )

    def _increment_counter(self, *, key: str, window_seconds: int) -> int:
        if cache.add(key, 1, timeout=window_seconds):
            return 1

        try:
            return int(cache.incr(key))
        except ValueError:
            cache.set(key, 1, timeout=window_seconds)
            return 1

    def _get_blocked_until(
        self,
        *,
        scope: str,
        ip_address: str,
        identifier: str,
    ):
        blocked_until_timestamp = cache.get(
            self._build_block_key(
                scope=scope,
                ip_address=ip_address,
                identifier=identifier,
            )
        )
        if blocked_until_timestamp is None:
            return None

        blocked_until = timezone.datetime.fromtimestamp(
            blocked_until_timestamp,
            tz=timezone.get_current_timezone(),
        )
        if blocked_until <= timezone.now():
            return None
        return blocked_until

    def _seconds_until(self, blocked_until) -> int:
        delta_seconds = (blocked_until - timezone.now()).total_seconds()
        return max(1, math.ceil(delta_seconds))

    def _build_counter_key(self, *, scope: str, ip_address: str, identifier: str) -> str:
        return f"{self._build_key_prefix(scope=scope, ip_address=ip_address, identifier=identifier)}:counter"

    def _build_block_key(self, *, scope: str, ip_address: str, identifier: str) -> str:
        return f"{self._build_key_prefix(scope=scope, ip_address=ip_address, identifier=identifier)}:blocked"

    def _build_key_prefix(self, *, scope: str, ip_address: str, identifier: str) -> str:
        normalized_identifier = (identifier or "").strip().lower()
        raw_key = f"{scope}|{ip_address}|{normalized_identifier}"
        digest = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        return f"employee-auth-rate-limit:{digest}"
