"""Closed target policy for the local OT laboratory."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from urllib.parse import urlsplit


class TargetKey(StrEnum):
    """Targets an authenticated user is allowed to select."""

    OT_GATEWAY_DEMO = "ot-gateway-demo"


class TargetPolicyError(ValueError):
    """Raised before network I/O when a target or endpoint is not allowed."""


@dataclass(frozen=True, slots=True)
class ResolvedTarget:
    """Server-owned target metadata passed to scanners."""

    key: TargetKey
    display_name: str
    base_url: str

    def url_for(self, endpoint: str) -> str:
        """Build a URL without allowing the endpoint to replace the origin."""
        if not isinstance(endpoint, str) or not endpoint.startswith("/"):
            raise TargetPolicyError("Scanner endpoints must start with a single slash")
        if endpoint.startswith("//") or "\\" in endpoint:
            raise TargetPolicyError("Absolute or ambiguous scanner endpoint rejected")
        if any(ord(character) < 32 for character in endpoint):
            raise TargetPolicyError("Control characters are not allowed in endpoints")

        parsed = urlsplit(endpoint)
        if parsed.scheme or parsed.netloc:
            raise TargetPolicyError("Scanner endpoint cannot override the target origin")
        return f"{self.base_url}{endpoint}"


class TargetPolicy:
    """Resolve one closed key to one fixed Docker-internal service."""

    _OT_GATEWAY_URL = "http://ot-gateway-demo:8081"

    @classmethod
    def resolve(
        cls,
        target: TargetKey,
        *,
        configured_url: str = _OT_GATEWAY_URL,
    ) -> ResolvedTarget:
        if not isinstance(target, TargetKey):
            raise TargetPolicyError("Only a declared target key is accepted")
        if target is not TargetKey.OT_GATEWAY_DEMO:
            raise TargetPolicyError("Unsupported scan target")
        if configured_url.rstrip("/") != cls._OT_GATEWAY_URL:
            raise TargetPolicyError("The OT gateway URL must remain Docker-internal and fixed")

        return ResolvedTarget(
            key=target,
            display_name="Water Pump Gateway",
            base_url=cls._OT_GATEWAY_URL,
        )

