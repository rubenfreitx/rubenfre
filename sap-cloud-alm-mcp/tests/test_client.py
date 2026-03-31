from sap_cloud_alm_mcp.client import SapCloudAlmClient
from sap_cloud_alm_mcp.config import Settings


def test_build_url_supports_relative_paths() -> None:
    client = SapCloudAlmClient(
        Settings(
            token_url="https://auth.example.com/oauth/token",
            api_base_url="https://tenant.alm.cloud.sap/api",
            client_id="client-id",
            client_secret="client-secret",
            scopes="",
            timeout_seconds=30,
        )
    )

    assert client._build_url("/operations/v1/events") == "https://tenant.alm.cloud.sap/api/operations/v1/events"
