import os
from dataclasses import dataclass
from typing import Literal, cast

GatewayProfile = Literal["vulnerable", "hardened"]


@dataclass(frozen=True, slots=True)
class Settings:
    profile: GatewayProfile
    jwt_secret: str
    demo_reset_key: str
    jwt_algorithm: str = "HS256"
    token_expire_minutes: int = 60
    auth_limit: int = 5
    command_limit: int = 5
    rate_window_seconds: int = 4

    @classmethod
    def from_env(cls) -> "Settings":
        raw_profile = os.getenv("OT_PROFILE", "vulnerable").lower()
        if raw_profile not in {"vulnerable", "hardened"}:
            raise RuntimeError("OT_PROFILE must be 'vulnerable' or 'hardened'")

        jwt_secret = os.getenv("OT_JWT_SECRET", "local-demo-jwt-secret-change-me")
        demo_reset_key = os.getenv("OT_DEMO_RESET_KEY", "local-demo-reset-key")
        if not jwt_secret or not demo_reset_key:
            raise RuntimeError("OT gateway secrets must not be empty")

        return cls(
            profile=cast(GatewayProfile, raw_profile),
            jwt_secret=jwt_secret,
            demo_reset_key=demo_reset_key,
        )
