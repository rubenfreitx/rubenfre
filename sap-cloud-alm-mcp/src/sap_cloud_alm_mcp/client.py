from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

import httpx

from sap_cloud_alm_mcp.config import Settings


class SapCloudAlmClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def get_access_token(self) -> dict[str, Any]:
        payload = {
            "grant_type": "client_credentials",
            "client_id": self._settings.client_id,
            "client_secret": self._settings.client_secret,
        }
        if self._settings.scopes:
            payload["scope"] = self._settings.scopes

        async with httpx.AsyncClient(timeout=self._settings.timeout_seconds) as client:
            response = await client.post(self._settings.token_url, data=payload)
            response.raise_for_status()
            return response.json()

    async def api_get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        token_response = await self.get_access_token()
        access_token = token_response["access_token"]
        url = self._build_url(path)
        headers = {"Authorization": f"Bearer {access_token}"}

        async with httpx.AsyncClient(timeout=self._settings.timeout_seconds) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                body: Any = response.json()
            else:
                body = response.text

        return {
            "url": url,
            "status_code": response.status_code,
            "content_type": content_type,
            "body": body,
        }

    def _build_url(self, path: str) -> str:
        if path.startswith("https://") or path.startswith("http://"):
            return path
        normalized_path = path if path.startswith("/") else f"/{path}"
        return urljoin(f"{self._settings.api_base_url}/", normalized_path.lstrip("/"))
