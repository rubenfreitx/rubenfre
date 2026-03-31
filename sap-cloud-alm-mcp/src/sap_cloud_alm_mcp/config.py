from __future__ import annotations

from dataclasses import dataclass
import os


REQUIRED_ENV_VARS = (
    "SAP_ALM_TOKEN_URL",
    "SAP_ALM_API_BASE_URL",
    "SAP_ALM_CLIENT_ID",
    "SAP_ALM_CLIENT_SECRET",
)


@dataclass(frozen=True)
class Settings:
    token_url: str
    api_base_url: str
    client_id: str
    client_secret: str
    scopes: str
    timeout_seconds: float

    @classmethod
    def from_env(cls) -> "Settings":
        timeout_raw = os.getenv("SAP_ALM_TIMEOUT_SECONDS", "30")
        return cls(
            token_url=os.getenv("SAP_ALM_TOKEN_URL", "").strip(),
            api_base_url=os.getenv("SAP_ALM_API_BASE_URL", "").strip().rstrip("/"),
            client_id=os.getenv("SAP_ALM_CLIENT_ID", "").strip(),
            client_secret=os.getenv("SAP_ALM_CLIENT_SECRET", "").strip(),
            scopes=os.getenv("SAP_ALM_SCOPES", "").strip(),
            timeout_seconds=float(timeout_raw),
        )

    def missing_fields(self) -> list[str]:
        missing: list[str] = []
        if not self.token_url:
            missing.append("SAP_ALM_TOKEN_URL")
        if not self.api_base_url:
            missing.append("SAP_ALM_API_BASE_URL")
        if not self.client_id:
            missing.append("SAP_ALM_CLIENT_ID")
        if not self.client_secret:
            missing.append("SAP_ALM_CLIENT_SECRET")
        return missing

    def sanitized(self) -> dict[str, object]:
        return {
            "token_url": self.token_url,
            "api_base_url": self.api_base_url,
            "client_id": mask_secret(self.client_id),
            "client_secret": mask_secret(self.client_secret),
            "scopes": self.scopes,
            "timeout_seconds": self.timeout_seconds,
            "missing_fields": self.missing_fields(),
        }


def mask_secret(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 6:
        return "*" * len(value)
    return f"{value[:3]}{'*' * (len(value) - 6)}{value[-3:]}"
