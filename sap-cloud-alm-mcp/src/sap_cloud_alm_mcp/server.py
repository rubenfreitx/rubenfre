from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from sap_cloud_alm_mcp.client import SapCloudAlmClient
from sap_cloud_alm_mcp.config import Settings


mcp = FastMCP("sap-cloud-alm")


def _settings() -> Settings:
    return Settings.from_env()


def _client() -> SapCloudAlmClient:
    return SapCloudAlmClient(_settings())


@mcp.tool()
def health_summary() -> dict[str, Any]:
    settings = _settings()
    return {
        "server": "sap-cloud-alm",
        "status": "ready" if not settings.missing_fields() else "missing-configuration",
        "configuration": settings.sanitized(),
    }


@mcp.tool()
def validate_environment() -> dict[str, Any]:
    settings = _settings()
    missing_fields = settings.missing_fields()
    return {
        "valid": not missing_fields,
        "missing_fields": missing_fields,
        "configuration": settings.sanitized(),
    }


@mcp.tool()
async def get_access_token(reveal_token: bool = False) -> dict[str, Any]:
    settings = _settings()
    if settings.missing_fields():
        return {
            "valid": False,
            "missing_fields": settings.missing_fields(),
        }

    token_response = await _client().get_access_token()
    if not reveal_token and "access_token" in token_response:
        token_response = {
            **token_response,
            "access_token": f"{token_response['access_token'][:12]}...",
        }
    return token_response


@mcp.tool()
async def api_get(path: str, params_json: str = "{}") -> dict[str, Any]:
    settings = _settings()
    if settings.missing_fields():
        return {
            "valid": False,
            "missing_fields": settings.missing_fields(),
        }

    params = _parse_params(params_json)
    return await _client().api_get(path=path, params=params)


def _parse_params(params_json: str) -> dict[str, Any]:
    if not params_json.strip():
        return {}
    parsed = json.loads(params_json)
    if not isinstance(parsed, dict):
        raise ValueError("params_json must be a JSON object")
    return parsed


def main() -> None:
    mcp.run()
